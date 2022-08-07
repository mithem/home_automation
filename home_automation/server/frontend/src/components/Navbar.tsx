import { Container, Nav, Navbar as RBNavbar } from "react-bootstrap";
import { useMediaPredicate } from "react-media-hook";
import { Link } from "react-router-dom";
import "../style/Navbar.css";
import ExternalLink from "./ExternalLink";
import { HEIMDALL_URL } from "../constants";

const Navbar = () => {
  const colorScheme = useMediaPredicate("(prefers-color-scheme: dark)")
    ? "dark"
    : "light";
  const heimdallLink =
    HEIMDALL_URL !== "" ? (
      <ExternalLink target={HEIMDALL_URL} title="Heimdall" />
    ) : null;
  return (
    <RBNavbar variant={colorScheme}>
      <Container>
        <RBNavbar.Brand>
          <Link className="inherit" to="/">
            Home Automation
          </Link>
        </RBNavbar.Brand>
        <RBNavbar.Toggle aria-controls="basic-navbar-nav" />
        <RBNavbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Link className="nav-link" to="/docker/containers">
              Containers
            </Link>
            <Link className="nav-link" to="/docker/volumes">
              Volumes
            </Link>
            <Link className="nav-link" to="/config">
              Config
            </Link>
            {heimdallLink}
          </Nav>
        </RBNavbar.Collapse>
      </Container>
    </RBNavbar>
  );
};

export default Navbar;
