import argparse
import logging
import time

from agent.config import settings
from agent.communication import BackendClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("westwood-endpoint-agent")


def main():
    parser = argparse.ArgumentParser(
        description="Westwood authorized endpoint monitoring agent"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Enroll if necessary and submit one monitoring report.",
    )

    args = parser.parse_args()
    client = BackendClient()

    try:
        if not client.device_token:
            logger.info("Starting authorized device enrollment...")
            enrollment = client.enroll()

            logger.info(
                "Enrollment completed. Device ID: %s",
                enrollment["device_id"],
            )
            logger.info("Device credential saved securely.")

        logger.info("Endpoint monitoring started.")

        while True:
            try:
                heartbeat = client.heartbeat()
                report = client.submit_monitoring_report()

                logger.info(
                    "Heartbeat: %s | Monitoring report: %s",
                    heartbeat.get("status", "received"),
                    report.get("report_id", "received"),
                )

            except Exception:
                logger.exception(
                    "Monitoring communication failed. "
                    "The agent will retry during the next cycle."
                )

            if args.once:
                break

            interval = max(30, settings.report_interval)
            logger.info("Next monitoring cycle in %s seconds.", interval)
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Monitoring stopped by the local operator.")

    except Exception:
        logger.exception("Endpoint agent could not start.")
        raise

    finally:
        client.close()


if __name__ == "__main__":
    main()
