import { Container, Nav, Navbar as RBNavbar } from "react-bootstrap";
import { useMediaPredicate } from "react-media-hook";
import { Link } from "react-router-dom";
import "../style/Navbar.css";
import ExternalLink, { ExternalLinkType } from "./ExternalLink";

const Navbar = () => {
  const colorScheme = useMediaPredicate("(prefers-color-scheme: dark)")
    ? "dark"
    : "light";
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
            <Link
              className="nav-link"
              //className={getClassForActivity("/docker/containers")}
              to="/docker/containers"
            >
              Containers
            </Link>
            <Link
              //className={getClassForActivity("/docker/volumes")}
              className="nav-link"
              to="/docker/volumes"
            >
              Volumes
            </Link>
            <Link
              className="nav-link"
              //className={getClassForActivity("/testing")}
              to="/testing"
            >
              Testing
            </Link>
            <ExternalLink
              target={ExternalLinkType.truenasGUI}
              title="Truenas GUI"
            />
            <ExternalLink
              target={ExternalLinkType.homeassistant}
              title="Home Assistant"
            />
            <ExternalLink
              target={ExternalLinkType.portainer}
              title="Portainer"
            />
            <ExternalLink
              target={ExternalLinkType.nextcloud}
              title="Nextcloud"
            />
            <ExternalLink target={ExternalLinkType.plex} title="Plex" />
          </Nav>
        </RBNavbar.Collapse>
      </Container>
    </RBNavbar>
  );
};

export default Navbar;
