import argparse
import logging
import time

from agent.config import settings
from agent.communication import BackendClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("endpoint-agent")

def main():
    parser = argparse.ArgumentParser(
        description="Authorized Windows Endpoint Monitoring Agent"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Collect and submit one monitoring report",
    )

    args = parser.parse_args()

    client = BackendClient()

    try:
        if not client.device_token:
            logger.info("Starting device enrollment...")
            enrollment = client.enroll()

            logger.info(
                "Enrollment complete. Device ID: %s",
                enrollment["device_id"],
            )

            logger.warning(
                "Store the returned device token securely in the agent's "
                "local configuration before restarting."
            )

            return

        logger.info("Endpoint monitoring started.")

        while True:
            try:
                client.heartbeat()
                report = client.submit_monitoring_report()

                logger.info(
                    "Monitoring report submitted: %s",
                    report.get("report_id"),
                )

            except Exception:
                logger.exception("Unable to communicate with backend.")

            if args.once:
                break

            time.sleep(max(30, settings.report_interval))

    except KeyboardInterrupt:
        logger.info("Monitoring stopped by administrator.")

    finally:
        client.close()

if __name__ == "__main__":
    main()
