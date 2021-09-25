import DockerContainerData from "./DockerContainerData"

export default class DockerContainerDataList {
	constructor(props: {containers: Array<DockerContainerData>} = {containers: []}) {
		this.containers = props.containers
	}
	containers: DockerContainerData[]
}
