import sublime, sublime_plugin, yaml, re
from yaml.composer import Composer
from yaml.constructor import Constructor

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
      line = self.line_detector.line_num(query)
      view.run_command("goto_line", {"line": line})

class Node(object):
  def __init__(self, name, line):
    self.name = name
    self.line = line
    self.parent = None

  def __str__(self):
    return "Node(name=" + self.name + ", line=" + str(self.line) + ", parent=" + str(self.parent)

class LineDetector(object):
  def __init__(self, text):
    self.nodes = self.build_graph(text)

  def build_graph(self, text):
    loader = yaml.Loader(text)
    nodes = {}

    def compose_node(parent, index):
      line = loader.line
      node = Composer.compose_node(loader, parent, index)
      if type(node) is yaml.ScalarNode and index is None:
        nodes[node] = Node(node.value, line + 1)
      return node

    def construct_mapping(node, deep=False):
      mapping = Constructor.construct_mapping(loader, node, deep=deep)
      for key_node, value_node in node.value:
        if type(value_node) is yaml.MappingNode:
          for child_key_node, child_value_node in value_node.value:
            nodes[child_key_node].parent = key_node
      return mapping

    loader.compose_node = compose_node
    loader.construct_mapping = construct_mapping
    loader.get_single_data()
    return nodes

  def line_num(self, query):
    def node_matches_selectors(node, selectors):
      if not selectors: return True
      if not node: return False
      node_info = self.nodes[node]

      if re.search(selectors[0], node_info.name):
        return node_matches_selectors(node_info.parent, selectors[1:])
      else:
        return node_matches_selectors(node_info.parent, selectors)

      return False

    query_parts = query.split()
    query_parts.reverse()
    first_selector = query_parts.pop(0)

    line = 0
    for k in self.nodes:
      node_info = self.nodes[k]
      if re.search(first_selector, node_info.name) and node_matches_selectors(node_info.parent, query_parts):
        line = node_info.line
        break

    return line
