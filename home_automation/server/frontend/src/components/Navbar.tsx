import {Container, Nav, Navbar as RBNavbar} from "react-bootstrap"
import {useMediaPredicate} from "react-media-hook"
import {Link} from "react-router-dom"
import "../style/Navbar.css"

function isActive(path: string) {
	if (document.location.pathname === path) {
		return true
	}
	return false
}

function getClassForActivity(path: string) {
	const standard = "nav-link "
	switch (isActive(path)) {
		case true: {
			return standard + "active"
		}
		default: {
			return standard
		}
	}
}

 const Navbar = () => {
	const colorScheme = useMediaPredicate("(prefers-color-scheme: dark)") ? "dark": "light"
	return (
		<RBNavbar variant={colorScheme}>
			<Container>
				<RBNavbar.Brand><Link className="inherit" to="/">Home Automation</Link></RBNavbar.Brand>
				<RBNavbar.Toggle aria-controls="basic-navbar-nav" />
				<RBNavbar.Collapse id="basic-navbar-nav">
					<Nav className="me-auto">
						<Link
						className="nav-link"
						//className={getClassForActivity("/docker/containers")}
						to="/docker/containers"
						>Containers</Link>
						<Link
						//className={getClassForActivity("/docker/volumes")}
						className="nav-link"
						to="/docker/volumes"
						>Volumes</Link>
						<Link
						className="nav-link"
						//className={getClassForActivity("/testing")}
						to="/testing">Testing</Link>
					</Nav>
				</RBNavbar.Collapse>
			</Container>
		</RBNavbar>
	)
}

export default Navbar
