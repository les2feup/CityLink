class ActDictElement:

    def __init__(self, callback=None, node_name=None, children=None):
        self.callback = callback
        self.node_name = node_name
        self.children = children if children is not None else {}


class ActionHandler:

    def __init__(self, ssa_instance):
        self._ssa = ssa_instance
        self.actions = {}

    def _find_dedicated_handler(self, action_uri):
        parts = action_uri.split('/')
        if parts[0] not in self.actions:
            return None
        current_node = self.actions[parts[0]]
        kwargs = {}
        for part in parts[1:]:
            if part in current_node.children:
                current_node = current_node.children[part]
            elif '*' in current_node.children:
                current_node = current_node.children['*']
                if current_node.node_name is not None:
                    kwargs[current_node.node_name] = part
            else:
                return None
        if current_node.callback is not None:
            return current_node.callback, kwargs
        return None

    def global_handler(self, action_uri, payload):
        if action_uri is None or len(action_uri) == 0:
            print('[WARNING] Received message from invalid topic. Ignoring.')
            return
        if action_uri in self.actions:
            handler = self.actions[action_uri].callback
            try:
                print(f'[DEBUG] Invoking action handler `{handler.__name__}`')
                self._ssa.create_task(handler, payload)
            except Exception as e:
                print(
                    f'[ERROR] Action callback `{handler.__name__}` failed to execute: {e}'
                    )
            return
        found = self._find_dedicated_handler(action_uri)
        if found is None:
            print(f'[ERROR] No action handler found for `{action_uri}`')
            return
        handler, kwargs = found
        try:
            print(
                f'[DEBUG] Invoking action handler `{handler.__name__}` with kwargs `{kwargs}`'
                )
            self._ssa.create_task(handler, payload, **kwargs)
        except Exception as e:
            func_name = handler.__name__ if hasattr(handler, '__name__'
                ) else 'unknown'
            print(
                f'[ERROR] Action callback `{func_name}` with kwargs `{kwargs}` failed to execute: {e}'
                )

    def register_action(self, action_uri, handler_func):
        if '{' not in action_uri:
            if action_uri in self.actions:
                raise Exception(
                    f'[ERROR] callback for `{action_uri}` already exists')
            self.actions[action_uri] = ActDictElement(callback=handler_func)
            return
        uri_parts = action_uri.split('/')
        if uri_parts[0].startswith('{'):
            raise Exception(
                '[ERROR] URI parameter cannot be the first part of an action name'
                )
        first_part = uri_parts[0]
        if first_part not in self.actions:
            self.actions[first_part] = ActDictElement()
        current_node = self.actions[first_part]
        current_dict = current_node.children
        for part in uri_parts[1:]:
            if part.startswith('{') and part.endswith('}'):
                var_name = part[1:-1]
                key = '*'
                if key not in current_dict:
                    current_dict[key] = ActDictElement(node_name=var_name)
                elif current_dict[key].node_name is None:
                    current_dict[key].node_name = var_name
                current_node = current_dict[key]
            else:
                key = part
                if key not in current_dict:
                    current_dict[key] = ActDictElement()
                current_node = current_dict[key]
            if part != uri_parts[-1]:
                current_dict = current_node.children
        if current_node.callback is not None:
            raise Exception(
                f'[ERROR] callback for `{action_uri}` already exists')
        current_node.callback = handler_func
