import { BASE_URL } from "./constants";
import axios from "axios";
import HomeAutomationManagementData from "./models/HomeAutomationManagementData";
import DockerContainerData from "./models/DockerContainerData";
import DockerVolumeListData from "./models/DockerVolumeListData";
import HomeAutomationStatus from "./models/HomeAutomationStatus";

const axiosDefaultConfig = {
  // for axios to handle the response as a response (not an error) when the status code isn't 2xx
  // useful for error handling with the response data
  validateStatus: (status: number) => {
    return status >= 200;
  },
};

export async function stopContainer(container: string) {
  const res = await axios.post(
    BASE_URL + "/api/containers/stop",
    {
      container: container,
    },
    axiosDefaultConfig
  );
  return res.status === 200;
}

export async function startContainer(container: string) {
  const res = await axios.post(
    BASE_URL + "/api/containers/start",
    {
      container: container,
    },
    axiosDefaultConfig
  );
  return res.status === 200;
}

export async function removeContainer(container: string) {
  const res = await axios.post(
    BASE_URL + "/api/containers/remove",
    {
      container: container,
    },
    axiosDefaultConfig
  );
  return res.status === 200;
}

export async function getDockerContainers() {
  const res = await axios.get(BASE_URL + "/api/containers", axiosDefaultConfig);
  if (res.status >= 400) {
    throw Error(res.data as string);
  }
  const data = res.data as { containers: DockerContainerData[] };
  if (data === null) {
    throw Error(res.data as string);
  }
  return data;
}

export async function composePull() {
  const res = await axios.post(
    BASE_URL + "/api/compose/pull",
    axiosDefaultConfig
  );
  return res.status === 202;
}

export async function composeUp() {
  const res = await axios.post(
    BASE_URL + "/api/compose/up",
    axiosDefaultConfig
  );
  return res.status === 202;
}

export async function composeDown() {
  const res = await axios.post(
    BASE_URL + "/api/compose/down",
    axiosDefaultConfig
  );
  return res.status === 202;
}

export async function getStatus() {
  const response = await axios.get(
    BASE_URL + "/api/status",
    axiosDefaultConfig
  );
  return response.data as HomeAutomationStatus;
}

export async function resetStatus() {
  const response = await axios.delete(
    BASE_URL + "/api/status",
    axiosDefaultConfig
  );
  return response.status === 200;
}

export async function dockerPrune() {
  const response = await axios.delete(
    BASE_URL + "/api/prune",
    axiosDefaultConfig
  );
  return response.status === 202;
}

export async function getHomeAutomationManagementData() {
  const response = await axios.get(
    BASE_URL + "/api/home_automation/versioninfo",
    axiosDefaultConfig
  );
  return response.data as HomeAutomationManagementData;
}

export async function refreshVersionInfo() {
  const response = await axios.post(
    BASE_URL + "/api/home_automation/versioninfo/refresh",
    null,
    axiosDefaultConfig
  );
  return response.status === 202;
}

export async function upgradeServer() {
  const response = await axios.post(
    BASE_URL + "/api/home_automation/upgrade",
    null,
    axiosDefaultConfig
  );
  if (response.status >= 400) {
    return { success: false, error: new Error(response.data as string) };
  }
  const success = response.status >= 200 && response.status <= 299; // that's what I call future-proofing (I know, I know..)
  return { success: success, error: undefined };
}

export async function getVolumes() {
  const res = await axios.get(BASE_URL + "/api/volumes", axiosDefaultConfig);
  if (res.status >= 400) {
    throw Error(res.data as string);
  }
  const data = res.data as DockerVolumeListData;
  if (data === null) {
    throw Error(res.data as string);
  }
  return data;
}

export async function removeVolume(id: string) {
  const response = await axios.post(
    BASE_URL + "/api/volumes/remove",
    { volume: id },
    axiosDefaultConfig
  );
  return response.status === 200;
}

export async function testingSetVersionAvailable() {
  const version = prompt("New version:");
  const response = await axios.post(
    BASE_URL + "/api/testing/version-initfile/set",
    { VERSION: version },
    axiosDefaultConfig
  );
  return response.status === 200;
}

export async function testingInitiateAutoUpgrade() {
  const response = await axios.post(
    BASE_URL + "/api/home_automation/autoupgrade",
    null,
    axiosDefaultConfig
  );
  return response.status === 202;
}

export async function upgradeHomeAssistant() {
  const response = await axios.post(
    BASE_URL + "/api/update-home-assistant",
    null,
    axiosDefaultConfig
  );
  if (response.status >= 400) {
    return {
      success: false,
      error: new Error(response.data as string),
      newVersion: undefined,
    };
  }
  return {
    success: true,
    error: undefined,
    newVersion: response.data.new_version,
  };
}

export async function forceHomeAssistantUpdate(forcedVersion: string) {
  try {
    await axios.post(
      BASE_URL + "/api/update-home-assistant",
      { update_to_version: forcedVersion },
      axiosDefaultConfig
    );
    return { success: true, error: undefined };
  } catch (error) {
    return { success: false, error: error as Error };
  }
}

export async function compress() {
  await axios.post(BASE_URL + "/api/compress", null, axiosDefaultConfig);
}

export async function archive() {
  await axios.post(BASE_URL + "/api/archive", null, axiosDefaultConfig);
}

export async function reloadConfig() {
  await axios.post(BASE_URL + "/api/config/reload", null, axiosDefaultConfig);
}

export function requestGoogleOAuth2() {
  window.open(BASE_URL + "/backend/home_automation/oauth2/google/request");
}

export async function sendTestMail() {
  try {
    await axios.post(BASE_URL + "/api/mail/test", null, axiosDefaultConfig);
  } catch (e) {
    requestGoogleOAuth2();
  }
}

export async function revokeGoogleOAuth() {
  await axios.post(
    BASE_URL + "/api/home_automation/oauth2/google/revoke",
    null,
    axiosDefaultConfig
  );
}

export async function clearGoogleOAuth() {
  await axios.delete(
    BASE_URL + "/api/home_automation/oauth2/google/clear",
    axiosDefaultConfig
  );
}

export async function restartHomeAutomation() {
  await axios.post(
    BASE_URL + "/api/home_automation/restart",
    null,
    axiosDefaultConfig
  );
}

export async function buildFrontend() {
  await axios.post(
    BASE_URL + "/api/home_automation/frontend/build",
    null,
    axiosDefaultConfig
  );
}

export async function deployFrontend() {
  await axios.post(
    BASE_URL + "/api/home_automation/frontend/deploy",
    null,
    axiosDefaultConfig
  );
}

export async function resetFrontendImageStatus() {
  await axios.delete(
    BASE_URL + "/api/home_automation/frontend/reset-image-status",
    axiosDefaultConfig
  );
}
