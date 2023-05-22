# P2P-File-Transfer-Application
A Peer-to-Peer (P2P) file transfer system that allows peers to obtain all the chunks of a file-set from other peers through a Tracker Server which keeps tracks of location of chunks of files.

## Features

- P2PClient:
  - Connects to a "well-known" P2PTracker server.
  - Reads a file named `local_chunks.txt` to determine the chunks already present in the P2PClient's folder.
  - Computes the hash of each file and sends this information to the P2PTracker++.
  - Asks the P2PTracker++ for the location of other P2PClients that have the remaining chunks.
  - Establishes TCP connections with other P2PClients to obtain the file chunks.
  - Updates the P2PTracker++ with the new chunk it has obtained.

- P2PTracker:
  - Starts on a "well-known" IP address and port number.
  - Accepts connections from multiple P2PClients simultaneously.
  - Maintains a check_list and chunk_list to keep track of file chunk information.
  - Moves entries from the check_list to the chunk_list when multiple P2PClients agree on the hash of a file chunk.
  - Responds to P2PClients' requests for chunk locations.

## Getting Started

To run the P2P file transfer system, follow these steps:

1. Clone the repository: `git clone https://github.com/your-username/p2p-file-transfer.git`
2. Change to the project directory: `cd p2p-file-transfer`
3. Compile and run the P2PTracker++ program: `python p2ptracker.py`
4. Open a new terminal window.
5. Compile and run the P2PClient program: `python p2pclient.py -folder <my-folder-full-path> -transfer_port <transfer-port-num> -name <entity-name>`
   - Replace `<my-folder-full-path>` with the full path to the folder containing the files.
   - Replace `<transfer-port-num>` with the desired port number for the P2PClient's transfer connection.
   - Replace `<entity-name>` with the name of the P2PClient entity.
6. Repeat step 5 to run additional P2PClients.
7. Interact with the P2PClient and observe the file transfer process.

## File Structure

The repository contains the following files:

- `p2pclient.py`: Implementation of the P2PClient program.
- `p2ptracker.py`: Implementation of the P2PTracker program.
- `local_chunks.txt`: File used by P2PClient to determine the chunks present in its folder.
- `README.md`: Project documentation and instructions.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Acknowledgments

This project was developed as an assignment for [Course Name] at [University Name]. We would like to thank our instructor for the guidance and support throughout the project.

