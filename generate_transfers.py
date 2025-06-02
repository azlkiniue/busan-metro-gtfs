import csv
import json

# csv header for transfers.txt
# from_stop_id,to_stop_id,transfer_type,min_transfer_time
header = [
    "from_stop_id",
    "to_stop_id",
    "transfer_type",
    "min_transfer_time"
]

transfers_list = [
  ["119", "219"], # Seomyeon
  ["123", "305"], # Yeonsan
  ["125", "402"], # Dongnae
  ["208", "301"], # Suyeong
  ["233", "313"], # Deokcheon
  ["309", "401"], # Minam
]

with open("transfers.txt", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    # write the header
    writer.writerow(header)
    
    # iterate through transfers and write to transfers.txt
    for transfer in transfers_list:
        from_stop_id, to_stop_id = transfer
        # write the row with transfer_type 2 and min_transfer_time 180
        writer.writerow([from_stop_id, to_stop_id, 2, 180])
        # also write the reverse order for the transfer
        writer.writerow([to_stop_id, from_stop_id, 2, 180])