#!/bin/bash
# Setup Transmission daemon as a background service

set -e

echo "========================================================================"
echo "Transmission Daemon Setup"
echo "========================================================================"
echo

# Check if running as root (needed for systemd service)
if [ "$EUID" -ne 0 ]; then
    echo "This script needs sudo access to:"
    echo "  - Install transmission-daemon"
    echo "  - Enable systemd service"
    echo
    echo "Re-running with sudo..."
    exec sudo bash "$0" "$@"
fi

# Get the actual user (not root if using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$ACTUAL_USER)

echo "Installing transmission-daemon..."
echo "------------------------------------------------------------------------"
apt update
apt install -y transmission-daemon transmission-cli
echo

echo "✓ Packages installed"
echo

# Stop the daemon if it's running
echo "Stopping transmission-daemon (if running)..."
systemctl stop transmission-daemon 2>/dev/null || true
echo

# Configure the daemon to run as the user
echo "Configuring daemon to run as user: $ACTUAL_USER"
echo "------------------------------------------------------------------------"

# Edit the systemd service file to run as the actual user
SERVICE_FILE="/lib/systemd/system/transmission-daemon.service"
if [ -f "$SERVICE_FILE" ]; then
    # Backup original
    cp "$SERVICE_FILE" "$SERVICE_FILE.backup"

    # Update User= line
    sed -i "s/^User=.*/User=$ACTUAL_USER/" "$SERVICE_FILE"

    echo "✓ Service configured to run as $ACTUAL_USER"
else
    echo "⚠ Service file not found at $SERVICE_FILE"
fi
echo

# Use existing settings from transmission-gtk
echo "Configuring daemon settings..."
echo "------------------------------------------------------------------------"

# The daemon uses different config locations depending on how it's run
# When run as a service under a user, it should use ~/.config/transmission-daemon/
DAEMON_CONFIG_DIR="$USER_HOME/.config/transmission-daemon"

# Create daemon config directory
mkdir -p "$DAEMON_CONFIG_DIR"
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$DAEMON_CONFIG_DIR"

# Copy existing settings from transmission-gtk if they exist
GTK_CONFIG="$USER_HOME/.config/transmission/settings.json"
DAEMON_CONFIG="$DAEMON_CONFIG_DIR/settings.json"

if [ -f "$GTK_CONFIG" ]; then
    echo "Copying settings from transmission-gtk..."
    cp "$GTK_CONFIG" "$DAEMON_CONFIG"

    # Ensure RPC is enabled
    sudo -u "$ACTUAL_USER" sed -i 's/"rpc-enabled": false/"rpc-enabled": true/' "$DAEMON_CONFIG"

    chown "$ACTUAL_USER:$ACTUAL_USER" "$DAEMON_CONFIG"
    echo "✓ Settings copied and RPC enabled"
else
    echo "⚠ No existing transmission-gtk config found"
    echo "  Daemon will use default settings"
fi
echo

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload
echo

# Enable the service to start on boot
echo "Enabling transmission-daemon service..."
systemctl enable transmission-daemon
echo "✓ Service enabled (will start on boot)"
echo

# Start the service
echo "Starting transmission-daemon..."
systemctl start transmission-daemon
echo

# Check status
echo "Checking service status..."
echo "------------------------------------------------------------------------"
sleep 2
systemctl status transmission-daemon --no-pager -l | head -20
echo

# Verify RPC is accessible
echo "Verifying RPC connection..."
echo "------------------------------------------------------------------------"
sleep 2

if command -v transmission-remote &> /dev/null; then
    if transmission-remote -l &> /dev/null; then
        echo "✓ RPC connection successful!"
        echo
        transmission-remote -l
    else
        echo "⚠ Could not connect to RPC"
        echo "  Try: transmission-remote -l"
    fi
else
    echo "⚠ transmission-remote not found in PATH"
    echo "  Install with: sudo apt install transmission-cli"
fi
echo

echo "========================================================================"
echo "Setup Complete!"
echo "========================================================================"
echo
echo "Transmission daemon is now running as a system service."
echo
echo "Service management commands:"
echo "  sudo systemctl status transmission-daemon   # Check status"
echo "  sudo systemctl start transmission-daemon    # Start service"
echo "  sudo systemctl stop transmission-daemon     # Stop service"
echo "  sudo systemctl restart transmission-daemon  # Restart service"
echo "  sudo systemctl disable transmission-daemon  # Disable auto-start"
echo
echo "Access methods:"
echo "  - RPC: http://localhost:9091"
echo "  - CLI: transmission-remote -l"
echo "  - GUI: transmission-remote-gtk (install separately)"
echo
echo "Configuration:"
echo "  - Config: $DAEMON_CONFIG_DIR/settings.json"
echo "  - To change settings: stop daemon, edit config, start daemon"
echo
echo "Note: Stop the daemon before editing settings.json:"
echo "  sudo systemctl stop transmission-daemon"
echo "  nano $DAEMON_CONFIG_DIR/settings.json"
echo "  sudo systemctl start transmission-daemon"
echo
