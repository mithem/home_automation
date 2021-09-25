export default interface DockerContainerData {
  	name: string
  	state: string
	image: DockerImage
	readonly key: string
}

interface DockerImage {
	tags: string[]
}
