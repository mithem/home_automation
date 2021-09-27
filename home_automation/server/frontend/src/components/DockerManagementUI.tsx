import React from "react"
import DockerContainer from "./DockerContainer"
import DockerContainerData from "../models/DockerContainerData"
import DockerVolumeData from "../models/DockerVolumeData"
import Toolbar from "./Toolbar"
import DockerVolume from "./DockerVolume"
import { refreshInterval } from "../constants"
import {Alert, Spinner} from "react-bootstrap"

import "../style/DockerManagementUI.css"
import {getDockerContainers, getVolumes} from "../functions"

export default class DockerManagmentUI extends React.Component<{}, {containers: DockerContainerData[], volumes: DockerVolumeData[], error?: Error, loading: boolean}> {
	containerTimer: any // either, I declare this as `number` and componentDidMount can't assign value of type `Timeout` to timerID or I declare this as `Timeout`, which then can't be found in current context!?
	// my justification: https://spin.atomicobject.com/2018/11/08/countdown-timer-react-typescript/
	volumeTimer: any
	constructor(props: any) {
		super(props)
		this.state = {containers: [], volumes: [], error: undefined, loading: false}
		this.containerTimer = -1
		this.volumeTimer = -1
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

	getVolumes() {
		if (!this.state.loading) {
			getVolumes()
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

		const volumeList = this.state.volumes.map((volume) => {
			return <DockerVolume volume={volume} key={volume.id} />
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

		const noVolumesWarning = this.state.volumes.length === 0 ? (
			<Alert variant="info">
				You currently don't have any docker volumes. Create some (e.g. by creating a container) to view them here.
			</Alert>
		) : null

		const loadingSpinner = this.state.loading ? (
			<Spinner animation="border"/>
		) : null

		return (
			<div className="docker-management-ui">
				<Toolbar />
				{apiError}
				{loadingSpinner}
				<h3>Containers</h3>
				<div className="item-list container-list">
					{noContainersWarning}
					{containerList}
				</div>
				<hr />
				<h3>Volumes</h3>
				<div className="item-list volume-list">
					{noVolumesWarning}
					{volumeList}
				</div>
			</div>
		)
	}
	componentDidMount() {
		this.getDockerContainers()
		this.getVolumes()
		this.containerTimer = setInterval(() => {
			this.getDockerContainers()
		}, refreshInterval)
		this.volumeTimer = setInterval(() => {
			this.getVolumes()
		}, refreshInterval)
	}
	componentWillUnmount() {
		clearInterval(this.containerTimer)
		clearInterval(this.volumeTimer)
	}
}
