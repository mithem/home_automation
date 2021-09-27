import React from "react"
import {Button} from "react-bootstrap"
import {testingSetVersionAvailable} from "../functions"

export default class TestingManagementUI extends React.Component {
	setVersionAvailable() {
		testingSetVersionAvailable()
	}
	render() {
		return (
			<div className="testing-management">
				<Button variant="primary" onClick={() => this.setVersionAvailable()}>
					Set version available
				</Button>
			</div>
		)
	}
}
