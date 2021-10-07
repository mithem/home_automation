import React from "react"
import {Alert, Spinner} from "react-bootstrap"

import DockerContainerData from "../models/DockerContainerData"
import DockerContainer from "./DockerContainer"
import {getDockerContainers} from "../functions"
import {refreshInterval} from "../constants"
import Toolbar from "./Toolbar"

export default class DockerContainerManagementUI extends React.Component<{}, {containers: DockerContainerData[], error?: Error, loading: boolean}> {
	timerID: any
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

		const noContainersWarning = this.state.containers.length === 0 ? (
			<Alert variant="info">
				You don't have any docker containers. Create some to see them here.
			</Alert>
		) : null

		const apiError = this.state.error !== undefined ? (
			<Alert variant="danger">
				There was an error fetching the containers: {this.state.error.message}
			</Alert>
		) : null

		const loadingSpinner = this.state.loading ? (
			<Spinner animation="border"/>
		) : null

		return (
			<div className="item-list container-list">
				<Toolbar />
				{apiError}
				{noContainersWarning}
				{loadingSpinner}
				{containerList}
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
