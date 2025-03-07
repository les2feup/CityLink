export interface Version {
  instance: string;
  model: string;
}

export interface RegistrationPayload {
  uuid: string;
  model: string;
  version: Version;
}
