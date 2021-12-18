#pridejte si podle vzoru sve volani... myslim ze nam to usetri cas a nervy
#EXAMPLE volani: sh run_test.sh X       (kde X je cislo, oznacujici co se spusti)

case $1 in

  1)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 1 --ai dt.stei xkuder04.xkuder04 -l logy # 1 HRA dt.stei 
    ;;

  2)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 10 --ai dt.stei xkuder04.xkuder04 -l logy # 10 HER dt.stei 
    ;;

  3)
    python3 ./scripts/dicewars-tournament.py -r -g 2 -n 50 --ai-under-test xkuder04.xkuder04 -b 101 -s 1337 -l logy # EVALUEATION TOURNAMENT
    ;;

  4)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 1 --ai kb.stei_at xkuder04.xkuder04 -l logy # 1 HRA kb.stei_at
    ;;

  5)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 10 --ai kb.stei_at xkuder04.xkuder04 -l logy # 10 HER kb.stei_at
    ;;

  6)
    python3 ./scripts/dicewars-human.py --ai kb.stei_at xkuder04.xkuder04 -l logy #HRA HUMAN
    ;;

  7)
    python3 ./scripts/dicewars-human.py --ai xkuder04.xkuder04 -l logy #HRA HUMAN SOLO
    ;;

  8)
    python3 ./scripts/dicewars-tournament.py -r -g 4 -n 50 --ai-under-test xkuder04.xkuder04 -b 101 -s 1337 -l logy # EVALUEATION TOURNAMENT 4
    ;;

  *)
    echo "Unknown argument"
    ;;
esac