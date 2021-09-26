export default interface HomeAutomationManagementData {
	version?: string
	available?: VersionAvailable
	error?: Error
}

interface VersionAvailable {
	version: string
	availableSince: Date
}
