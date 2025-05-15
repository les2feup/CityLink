export interface Version {
  instance: string;
  model: string;
}

export interface RegistrationPayload {
  tmTitle?: string;
  tmHref: string;
  version: Version;
}
