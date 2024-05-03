from typing import Dict, List


def initialize_object(class_name: str, class_configuration: dict) -> object:
    """
    Initializes a class from the Plugin Registry
    :param class_name: the class name
    :param class_configuration: the required and optional fields treated as **kwargs
    :return: an object
    """
    from registry import PluginRegistry
    result = PluginRegistry.objects[class_name](**class_configuration)
    return result


def initialize_objects(list_dict: List[Dict]) -> List[object]:
    result = [initialize_object(class_name=object_name,
                                class_configuration=object_configuration)
              for d in list_dict
              for object_name, object_configuration in d.items()]

    return result
