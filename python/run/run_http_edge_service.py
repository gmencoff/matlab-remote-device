#!/usr/bin/env python3
"""
Test the HTTP edge service.
"""

from src.httpservice.http_edge_service import HttpEdgeService


def main():
    """Main function to set up and run the fake Pluto with Firebase edge service."""
    
    service = HttpEdgeService(device_id="test-device")
    service.activate_topic("test-topic")


if __name__ == "__main__":
    main()