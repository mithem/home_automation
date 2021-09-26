import React from "react";

import DockerManagementUI from "./components/DockerManagementUI"
import HomeAutomationManagementUI from "./components/HomeAutomationManagementUI";
import Navbar from "./components/Navbar";

import "./style/App.css"

export default class App extends React.Component {
	render() {
		return (
			<div className="App">
				<Navbar />
				<DockerManagementUI />
				<hr />
				<HomeAutomationManagementUI />
			</div>
		)
	}
}
