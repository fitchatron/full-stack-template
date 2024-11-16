type Event = {
  type: "error" | "info";
  message: string;
};

export function eventLogger(event: Event) {
  function logEvent() {
    switch (event.type) {
      case "error":
        console.log("LOGGING>>>");
        console.error(event.message);
        break;
      case "info":
        console.log("LOGGING>>>");
        console.log(event.message);
        break;
      default:
        console.log("LOGGING>>>");
        console.log(event.message);
        break;
    }
  }

  return { logEvent };
}
