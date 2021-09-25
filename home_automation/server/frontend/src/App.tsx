import React from "react"
import DockerContainer from "./components/DockerContainer"
import DockerContainerData from "./components/DockerContainerData"
import DockerContainerDataList from "./components/DockerContainerDataList"
import Toolbar from "./components/Toolbar"
import { BASE_URL } from "./constants"
import {Alert, Spinner} from "react-bootstrap"

import "./style/App.css"

class InvalidResponseError extends Error {}

export default class App extends React.Component<{}, {containers: DockerContainerData[], error?: Error, loading: boolean}> { timerID: any // either, I declare this as `number` and componentDidMount can't assign value of type `Timeout` to timerID or I declare this as `Timeout`, which then can't be found in current context!?
	// my justification: https://spin.atomicobject.com/2018/11/08/countdown-timer-react-typescript/
	constructor(props: any) {
		super(props)
		this.state = {containers: [], error: undefined, loading: true}
		this.timerID = -1
	}
	getDockerContainers() {
		// don't set state.loading = true as the loading spinner shall only appear when first loading containers, not on every refresh
		fetch(BASE_URL + "/api/containers")
			.then(response => {this.parseContainerResponse(response)})
	}
	async parseContainerResponse(response: Response) {
		const text = await response.text()
		try {
			const data: {containers: DockerContainerData[]} = JSON.parse(text)
			if ( data === null ) {
				throw new InvalidResponseError("No data.")
			}
			this.setState({containers: new DockerContainerDataList(data).containers, error: undefined, loading: false})
		} catch (exception) {
			const e: Error = exception as Error
			if ( text !== "") {
				this.setState({error: Error(text), loading: false})
			} else {
				this.setState({error: e, loading: false})
			}
		}
	}
	render() {
		const containerList = this.state.containers.map((container) => {
			return <DockerContainer container={container} />
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
			<div className="App">
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
		}, 1000)
	}
	componentWillUnmount() {
		clearInterval(this.timerID)
	}
}
