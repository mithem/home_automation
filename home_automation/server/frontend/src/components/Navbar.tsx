import {Container, Nav, Navbar as RBNavbar} from "react-bootstrap"
import { useMediaPredicate } from "react-media-hook"
import "../style/Navbar.css"

function isActive(path: string) {
	if (document.location.pathname === path) {
		return true
	}
	return false
}

function getClassForActivity(path: string) {
	switch (isActive(path)) {
		case true: {
			return "active"
		}
		default: {
			return ""
		}
	}
}

 const Navbar = () => {
	const colorScheme = useMediaPredicate("(prefers-color-scheme: dark)") ? "dark": "light"
	return (
		<RBNavbar variant={colorScheme}>
			<Container>
				<RBNavbar.Brand href="/">Home Automation</RBNavbar.Brand>
				<RBNavbar.Toggle aria-controls="basic-navbar-nav" />
				<RBNavbar.Collapse id="basic-navbar-nav">
					<Nav className="me-auto">
						<Nav.Link className={getClassForActivity("/docker")} href="/docker">Docker</Nav.Link>
						<Nav.Link className={getClassForActivity("/testing")} href="/testing">Testing</Nav.Link>
					</Nav>
				</RBNavbar.Collapse>
			</Container>
		</RBNavbar>
	)
}

export default Navbar
