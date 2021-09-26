import React from "react"
import DockerContainer from "./DockerContainer"
import DockerContainerData from "../models/DockerContainerData"
import Toolbar from "./Toolbar"
import { refreshInterval } from "../constants"
import {Alert, Spinner} from "react-bootstrap"

import "../style/DockerManagementUI.css"
import {getDockerContainers} from "../functions"

export default class DockerManagmentUI extends React.Component<{}, {containers: DockerContainerData[], error?: Error, loading: boolean}> { timerID: any // either, I declare this as `number` and componentDidMount can't assign value of type `Timeout` to timerID or I declare this as `Timeout`, which then can't be found in current context!?
	// my justification: https://spin.atomicobject.com/2018/11/08/countdown-timer-react-typescript/
	constructor(props: any) {
		super(props)
		this.state = {containers: [], error: undefined, loading: false}
		this.timerID = -1
	}
	getDockerContainers() {
		// don't set state.loading = true as the loading spinner shall only appear when first loading containers, not on every refresh
		if (!this.state.loading) {
			getDockerContainers()
				.then(data => {
					this.setState(data)
					this.setState({error: undefined, loading: false})
				})
				.catch((error) => {
					this.setState({error: error as Error, loading: false})
				})
		}
	}

	render() {
		const containerList = this.state.containers.map((container) => {
			return <DockerContainer container={container} key={container.name}/>
		})

		const apiError = this.state.error !== undefined ? (
			<Alert variant="danger">
				There was an error fetching the containers: {this.state.error.message}
			</Alert>
		) : null

		const noContainersWarning = this.state.containers.length === 0 ? (
			<Alert variant="info">
				You don't have any docker containers. Create some to see them here.
			</Alert>
		) : null

		const loadingSpinner = this.state.loading ? (
			<Spinner animation="border"/>
		) : null

		return (
			<div className="docker-management-ui">
				<Toolbar />
				{apiError}
				{noContainersWarning}
				{loadingSpinner}
				<div className="container-list">
					{containerList}
				</div>
			</div>
		)
	}
	componentDidMount() {
		this.getDockerContainers()
		this.timerID = setInterval(() => {
			this.getDockerContainers()
		}, refreshInterval)
	}
	componentWillUnmount() {
		clearInterval(this.timerID)
	}
}
