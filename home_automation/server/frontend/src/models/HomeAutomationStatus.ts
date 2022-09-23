export default interface HomeAutomationStatus {
  pulling: boolean;
  upping: boolean;
  downing: boolean;
  pruning: boolean;
  building_frontend_image: boolean;
  pushing_frontend_image: boolean;
  updating: boolean;
}
