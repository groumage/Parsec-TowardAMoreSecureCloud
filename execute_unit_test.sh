if [ "$#" -ne 1 ]; then
    echo "You must enter exactly 1 argument: --terminal or --gui"
else
    if [[ "$1" == "--terminal" ]]
    then
        gnome-terminal -e "bash -c 'source tests/scripts/start_blockchain.sh /home/guillaume/Tendermint/tendermint'"
        sleep 5 # give time for tendermint to start
        gnome-terminal -- python3 -m pytest --blockchain --runslow -k backend/realm
    elif [[ "$1" == "--gui" ]]
    then
        gnome-terminal -e "bash -c 'source tests/scripts/start_blockchain.sh /home/guillaume/Tendermint/tendermint'"
        sleep 5 # give time for tendermint to start
        gnome-terminal -e "bash -c 'source tests/scripts/run_testenv.sh --db BLOCKCHAIN;python3 -m parsec.core.cli gui'"
    fi
fi
