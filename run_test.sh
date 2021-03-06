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
    python3 ./scripts/dicewars-tournament.py -r -g 2 -n 50 --ai-under-test xkuder04.xkuder04 -b 101 -s 1337 -l logy # EVALUEATION TOURNAMENT 2
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
    python3 ./scripts/dicewars-tournament.py -r -g 4 -n 50 --ai-under-test xkuder04.xkuder04 -l logy # EVALUEATION TOURNAMENT 4
    ;;

  9)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 1 --ai kb.stei_dt xkuder04.xkuder04 -l logy # 1 HRA kb.stei_dt
    ;;

  10)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 10 --ai kb.stei_dt xkuder04.xkuder04 -l logy # 10 HRA kb.stei_dt
    ;;

  11)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 1 --ai kb.stei_adt xkuder04.xkuder04 -l logy # 1 HRA kb.stei_adt
    ;;

  12)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 10 --ai kb.stei_adt xkuder04.xkuder04 -l logy # 10 HRA kb.stei_adt
    ;;

  13)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 1 --ai kb.sdc_pre_at xkuder04.xkuder04 -l logy # 1 HRA kb.sdc_pre_at
    ;;

  14)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 10 --ai kb.sdc_pre_at xkuder04.xkuder04 -l logy # 10 HRA kb.sdc_pre_at
    ;;

  15)
    python3 ./scripts/dicewars-tournament.py -r -g 4 -n 50 --ai-under-test xkuder04.xkuder04 -b 101 -s 1337 -l logy # EVALUEATION TOURNAMENT 4
    ;;

  16)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n 100 --ai kb.stei_at xkuder04.xkuder04 -l logy # 100 HER kb.stei_at
    ;;

  17)
    python3 ./scripts/dicewars-ai-only.py -r -b 11 -s 42 -n 400 --ai xkuder04-rf.xkuder04-rf xkuder04-rf-prep.xkuder04-rf-prep xkuder04-svm.xkuder04-svm xkuder04-svm-prep.xkuder04-svm-prep -l logy
    ;;

  *)
    echo "Unknown argument"
    ;;
esac