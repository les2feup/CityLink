export interface Version {
  instance: string;
  model: string;
}

export interface RegistrationPayload {
  name: string;
  href: string;
  version: Version;
}
