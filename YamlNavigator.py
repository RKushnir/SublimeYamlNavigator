import sublime, sublime_plugin, yaml, re

class YamlNavigatorCommand(sublime_plugin.WindowCommand):
  def run(self):
    view = self.window.active_view()

    if view:
      text = view.substr(sublime.Region(0, view.size()))
      self.line_detector = LineDetector(text)
      self.window.show_input_panel("Yaml Selector:", "", None, self.on_change, None)
    pass

  def on_change(self, query):
    view = self.window.active_view()
    if query and view:
      line = self.line_detector.line_num(query) + 1
      view.run_command("goto_line", {"line": line})

class Node(object):
  def __init__(self, name, line, parent):
    self.name = name
    self.line = line
    self.parent = parent

class LineDetector(object):
  def __init__(self, text):
    self.nodes = self.build_graph(text)

  def build_graph(self, text):
    events = yaml.parse(text)
    node_stack = [None]
    nodes = []

    mapping_changed = False
    for event in events:
      if type(event) is yaml.MappingStartEvent:
        mapping_changed = True
      else:
        if type(event) is yaml.MappingEndEvent:
          mapping_changed = True
          node_stack.pop()
        else:
          if type(event) is yaml.ScalarEvent:
            if mapping_changed:
              node = Node(event.value, event.start_mark.line, node_stack[-1])
              nodes.append(node)
              node_stack.append(node)

          mapping_changed = False

    return nodes

  def line_num(self, query):
    def node_matches_selectors(node, selectors):
      if not selectors: return True
      if not node: return False

      new_selectors = selectors[:-1] if re.search(selectors[-1], node.name) else selectors
      return node_matches_selectors(node.parent, new_selectors)

    query_parts = query.split()
    first_selector = query_parts.pop()

    line = 0
    for node in self.nodes:
      if re.search(first_selector, node.name) and node_matches_selectors(node.parent, query_parts):
        line = node.line
        break

    return line
