
class ServiceProviderDto:
  def __init__(self, name, title):
    self.name = name
    self.title = title

class ExtensionTypeDto:
  def __init__(self, name, title):
    self.name = name
    self.title = title

class ExtensionDto:
  def __init__(self, **kwargs):
    self.extension_code = kwargs.get('extension_code')
    self.title = kwargs.get('title')
    self.service_provider = ServiceProviderDto(**kwargs.get('service_provider', {}))
    self.extension_type = ExtensionTypeDto(**kwargs.get('extension_type', {}))
    self.major = kwargs.get('major')
    self.minor = kwargs.get('minor')
    self.description = kwargs.get('description')
    self.library_name = kwargs.get('library_name')
    self.is_background_plugin = kwargs.get('is_background_plugin')
    self.is_build_in = kwargs.get('is_build_in')
    self.file = kwargs.get('file')
    self.config = kwargs.get('config')

  def construct_name(self):
    return f"{self.service_provider.name}_{self.extension_type.name}_{self.extension_code}_v{self.major}.{self.minor}"

  def get_plugin_name(self):
    return f"{self.service_provider.name}_{self.extension_type.name}_{self.extension_code}"


class ServicePacketDto:
  
  def __init__(self, title: str, code_name: str, major: int, minor: int, is_system_packet: bool, description: str, service_provider, extensions):
    self.title = title
    self.code_name = code_name
    self.major = major
    self.minor = minor
    self.is_system_packet = is_system_packet
    self.description = description
    self.service_provider = ServiceProviderDto(**service_provider)
    self.extensions = [ExtensionDto(**extension) for extension in extensions]

  def construct_name(self):
    return f"{self.service_provider.name}_{self.code_name}"
  
  def construct_packet_version_name(self):
    return f"{self.construct_name()}_v{self.major}.{self.minor}"

  def get_distinct_extension_types(self):
    return list(set([extension.extension_type for extension in self.extensions]))
  
  def get_plugin_exensions(self) -> list[ExtensionDto]:
    return [extension for extension in self.extensions if extension.extension_type.name == 'PS Plugin' or extension.extension_type.name == 'MC Plugin']

  def get_web_applications(self) -> list[ExtensionDto]:
    return [extension for extension in self.extensions if extension.extension_type.name == 'Web Application']


class PacketDto:
  installed: bool
  def __init__(self, name, title, release_version, service_provider):
    self.name = name
    self.title = title
    self.release_version = release_version
    self.service_provider = service_provider
    self.installed = False

  def to_dict(self):
    return {
      'name': self.name,
      'title': self.title,
      'release_version': self.release_version,
      'service_provider': self.service_provider,
      'installed': self.installed
    }

  @classmethod
  def from_dict(cls, data):
    return cls(
      data['name'],
      data['title'],
      data['release_version'],
      data['service_provider']
    )
  # @property
  # def installed(self):
  #   return self._installed

  # @installed.setter
  # def installed(self, value):
  #   if isinstance(value, bool):
  #     self._installed = value
  #   else:
  #     raise ValueError("Installed must be a boolean value")


  