import React from "react"
import {Button} from "react-bootstrap"
import {testingSetVersionAvailable, testingInitiateAutoUpgrade} from "../functions"

export default class TestingManagementUI extends React.Component {

	setVersionAvailable() {
		testingSetVersionAvailable()
	}

	initiateAutoUpgrade() {
		testingInitiateAutoUpgrade()
	}

	render() {
		return (
			<div className="testing-management">
				<Button variant="primary" onClick={() => this.setVersionAvailable()}>
					Set version available
				</Button>
				<br />
				<Button variant="primary" onClick={() => this.initiateAutoUpgrade()}>
					Initiate auto upgrade
				</Button>
			</div>
		)
	}
}
