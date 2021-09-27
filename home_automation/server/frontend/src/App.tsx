import React from "react";

import DockerManagementUI from "./components/DockerManagementUI"
import HomeAutomationManagementUI from "./components/HomeAutomationManagementUI";
import Navbar from "./components/Navbar";
import ErrorNotFound from "./components/ErrorNotFound"

import "./style/App.css"

export default class App extends React.Component {
	render() {
		let content: any
		switch(document.location.pathname) {
			case "/docker": {
				content = <DockerManagementUI />
				break
			}
			case "/": {
				content = <HomeAutomationManagementUI />
				break
			}
			default: {
				content = <ErrorNotFound path={document.location.href}/>
			}
		}
		return (
			<div className="App">
				<Navbar />
				{content}
			</div>
		)
	}
}
