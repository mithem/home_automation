export default interface HomeAutomationManagementData {
  version?: string;
  available?: VersionAvailable;
  newHomeAssistantVersion?: string;
  versionAvailableFetchingError?: Error;
  homeAssistantUpdateError?: Error;
  upgradeServerError?: Error;
  otherError?: Error;
}

interface VersionAvailable {
  version: string;
  availableSince: Date;
}
