import HomeAutomationStatus from "../components/HomeAutomationStatus";

export default interface HomeAutomationManagementData {
  version?: string;
  available?: VersionAvailable;
  newHomeAssistantVersion?: string;
  versionAvailableFetchingError?: Error;
  homeAssistantUpdateError?: Error;
  upgradeServerError?: Error;
  otherError?: Error;
  status: HomeAutomationStatus;
}

interface VersionAvailable {
  version: string;
  availableSince: Date;
}
