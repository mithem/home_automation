import { BASE_URL } from "./constants"
import axios from "axios"
import HomeAutomationManagementData from "./models/HomeAutomationManagementData"
import DockerContainerData from "./models/DockerContainerData"

export async function stopContainer(container: string) {
	const res = await axios.post(BASE_URL + "/api/stop", {container: container})
	return res.status === 200
}

export async function startContainer(container: string) {
	const res = await axios.post(BASE_URL + "/api/start", {container: container})
	return res.status === 200
}

export async function removeContainer(container: string) {
	const res = await axios.post(BASE_URL + "/api/remove", {container: container})
	return res.status === 200
}

export async function getDockerContainers() {
	const res = await axios.get(BASE_URL + "/api/containers")
	const data = res.data as {containers: DockerContainerData[]}
	if (data === null) {
		throw Error(res.data as string)
	}
	return data
}

export async function composePull() {
	const res = await axios.post(BASE_URL + "/api/compose/pull")
	return res.status === 200
}

export async function composeUp() {
	const res = await axios.post(BASE_URL + "/api/compose/up")
	return res.status === 200
}

export async function composeDown() {
	const res = await axios.post(BASE_URL + "/api/compose/down")
	return res.status === 200
}

export async function dockerStatus() {
	const response = await axios.get(BASE_URL + "/api/status")
	return response.data as {pulling: boolean, upping: boolean, downing: boolean, pruning: boolean}
}

export async function dockerPrune() {
	const response = await axios.delete(BASE_URL + "/api/prune")
	return response.status === 200
}

export async function getHomeAutomationManagementData() {
	const response = await axios.get(BASE_URL + "/api/home_automation/versioninfo")
	return response.data as HomeAutomationManagementData
}

export async function refreshVersionInfo() {
	const response = await axios.post(BASE_URL + "/api/home_automation/versioninfo/refresh")
	return response.status === 200
}

export async function upgradeServer() {
	const response = await axios.post(BASE_URL + "/api/home_automation/upgrade")
	return response.status === 200
}
