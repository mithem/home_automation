import {Container, Nav, Navbar as RBNavbar} from "react-bootstrap"
import { useMediaPredicate } from "react-media-hook"

 const Navbar = () => {
	const colorScheme = useMediaPredicate("(prefers-color-scheme: dark)") ? "dark": "light"
	return (
		<RBNavbar variant={colorScheme}>
			<Container>
				<RBNavbar.Brand href="/">Home Automation</RBNavbar.Brand>
				<RBNavbar.Toggle aria-controls="basic-navbar-nav" />
				<RBNavbar.Collapse id="basic-navbar-nav">
					<Nav className="me-auto">
						<Nav.Link href="/docker">Docker</Nav.Link>
					</Nav>
				</RBNavbar.Collapse>
			</Container>
		</RBNavbar>
	)
}

export default Navbar
