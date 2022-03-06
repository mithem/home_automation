export default interface HomeAutomationManagementData {
  version?: string;
  available?: VersionAvailable;
  newHomeAssistantVersion?: string;
  versionAvailableFetchingError?: Error;
  homeAssistantUpdateError?: Error;
  upgradeServerError?: Error;
}

interface VersionAvailable {
  version: string;
  availableSince: Date;
}
