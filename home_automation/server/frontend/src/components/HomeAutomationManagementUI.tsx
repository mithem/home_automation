import React from "react";
import {Alert, Button} from "react-bootstrap";
import {refreshInterval} from "../constants";
import {getHomeAutomationManagementData, upgradeServer, refreshVersionInfo} from "../functions";
import HomeAutomationManagementData from "../models/HomeAutomationManagementData";

import "../style/HomeAutomationManagementUI.css"

export default class HomeAutomationManagementUI extends React.Component<{}, HomeAutomationManagementData> {
	timerID: any
	constructor(props: any) {
		super(props)
		this.state = {version: undefined, available: undefined, error: undefined}
		this.timerID = undefined
	}

	async getData() {
		getHomeAutomationManagementData()
			.then(data => {
				if (data.version === undefined) {
					this.setState({error: Error("No version data.")})
				}
				// a) undefine the error in one line
				// b) clear available version once it's no longer newer
				this.setState({version: data.version, available: data.available, error: undefined})
			})
			.catch((error) => {
				this.setState({version: undefined, available: undefined, error: error as Error})
			})
	}

	upgradeServer() {
		upgradeServer()
			.then(result => {
				if (!result.success) {
					this.setState({error: result.error})
				}
			})
	}

	render() {
		const newVersionAvailableAlert = this.state.available !== undefined ? (
			<Alert variant="success" className="version available">
				<span>A new version is available: {this.state.available.version} (checked {this.state.available.availableSince})!</span>
				<Button variant="primary" onClick={() => {this.upgradeServer()}}>
					Upgrade
				</Button>
			</Alert>
		) : null
		const errorAlert = this.state.error !== undefined ? (
			<Alert variant="danger">
				Error fetching version info: {this.state.error.message}
			</Alert>
		) : null
		return(
			<div className="home-automation-management-gui item-list">
				{errorAlert}
				<Alert variant="secondary" className="version current">
					<span>Current version: {this.state.version ?? "N/A"}</span>
					<Button variant="primary" onClick={refreshVersionInfo}>
						Check for updates
					</Button>
				</Alert>
				{newVersionAvailableAlert}
			</div>
		)
	}

	componentDidMount() {
		this.getData()
		this.timerID = setInterval(() => {
			this.getData()
		}, refreshInterval)
	}

	componentWillUnmount() {
		clearInterval(this.timerID)
	}
}
