# The Great Escape

**Category:** Web
**Difficulty:** Medium
**Author:** CTF Team

---

## Description

NexusHR is a modern enterprise human resources management system used by Fortune 500 companies worldwide. The IT department recently deployed a new employee directory search feature that interfaces directly with their PostgreSQL database through a streamlined command-line backend.

As part of a routine security assessment, you've been granted access to the employee search portal. Your objective is to identify any vulnerabilities in the system and retrieve sensitive HR data that should not be accessible through the public interface.

The developers assure us that all user input is properly sanitized before being passed to the database. They've implemented industry-standard quote escaping to prevent SQL injection attacks.

Can you find a way to escape their defenses?

## Challenge Information

- **URL:** http://localhost:5000
- **Flag Format:** `Exploit3rs{...}`

## Hints

1. Sometimes the path you take matters as much as the destination
2. What works in one context might behave differently in another
3. The classics don't always apply - think about how data flows through the system

## Setup

### Prerequisites
- Docker
- Docker Compose

### Running the Challenge

```bash
# Start the challenge
./run.sh start

# Check status
./run.sh status

# Stop the challenge
./run.sh stop

# View logs
./run.sh logs
```

The application will be available at `http://localhost:5000`

## Technical Notes

- The application uses a command-line database interface for query execution
- Input sanitization is performed at the application layer
- Standard database security measures are in place

---

Good luck, and remember: not all escapes are created equal.
