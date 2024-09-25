import tkinter as tk
from tkinter import ttk, messagebox
import os
import csv
from main import login_to_website, open_url, fetch_sender_data, fetch_message_templates
import time


def update_days(*args):
    """Update day values for start and end date based on selected month and year."""
    # Update days for the start date
    month = int(start_month_combo.get())
    year = int(start_year_combo.get())
    day_range = days[month - 1]
    if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
        day_range = 29
    start_day_values = [str(day).zfill(2) for day in range(1, day_range + 1)]
    start_day_combo['values'] = start_day_values
    if start_day_combo.get() not in start_day_values:
        start_day_combo.set(start_day_values[0])  # Reset to first day of the month if not in new range

    # Update days for the end date
    month = int(end_month_combo.get())
    year = int(end_year_combo.get())
    day_range = days[month - 1]
    if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
        day_range = 29
    end_day_values = [str(day).zfill(2) for day in range(1, day_range + 1)]
    end_day_combo['values'] = end_day_values
    if end_day_combo.get() not in end_day_values:
        end_day_combo.set(end_day_values[0])
        

def open_website():
    """Login to website and initialize listboxes."""
    login_to_website()
    time.sleep(5)
    init_sender_id_listbox()
    init_template_id_list()


def open_camp():
    """Validate and execute the opening of a campaign with selected parameters."""
    selected_senders = send_selected_senders()
    selected_template = send_selected_template()
    starting_hour = start_hour_combo.get()
    ending_hour = end_hour_combo.get()
    start_date = f"{start_year_combo.get()}/{start_month_combo.get().zfill(2)}/{start_day_combo.get().zfill(2)}"
    end_date = f"{end_year_combo.get()}/{end_month_combo.get().zfill(2)}/{end_day_combo.get().zfill(2)}"
    gap = gap_entry.get()
    
    if start_date > end_date:
        messagebox.showerror("Date Error", "End date cannot be before start date.")
        return
    

    if starting_hour == "Select Starting Hour" or ending_hour == "Select Ending Hour":
        messagebox.showerror("Hour Error", "Please select both starting and ending hours.")
        return
    

    if len(selected_senders) >= 1:
        open_url(selected_senders, selected_template, starting_hour, ending_hour, start_date, end_date, gap)
    else:
        messagebox.showerror("Selection Error", "Please select at least one sender to open the campaign.")

def init_template_id_list():
    """Fetch and display available message templates."""
    template_data = fetch_message_templates()
    template_names = list(template_data.values())
    template_id_combobox['values'] = template_names
    if template_names:
        template_id_combobox.current(0)

def init_sender_id_listbox():
    """Fetch and display available senders."""
    sender_data = fetch_sender_data()
    sender_listbox.delete(0, tk.END)
    for sender_id, sender_name in sender_data.items():
        sender_listbox.insert(tk.END, sender_name)
    sender_listbox.bind("<<ListboxSelect>>", update_selected_senders)
    

def update_selected_senders(event):
    """Update entry with selected senders' names on selection."""
    selected_indices = sender_listbox.curselection()
    selected_names = [sender_listbox.get(i) for i in selected_indices]
    selected_senders_entry.delete(0, tk.END)
    selected_senders_entry.insert(0, ", ".join(selected_names))

def send_selected_senders():
    """Retrieve names of selected senders."""
    selected_indices = sender_listbox.curselection()
    selected_names = [sender_listbox.get(i) for i in selected_indices]
    return selected_names

def send_selected_template():
    """Retrieve the selected message template or show error if none."""
    selected_template = template_id_combobox.get()
    if selected_template:
        return selected_template
    else:
        messagebox.showerror("Selection Error", "No template selected.")

def find_csv_filename(directory):
    """Find a .csv file in the specified directory."""
    for file in os.listdir(directory):
        if file.endswith(".csv"):
            return file
    return None

def split_csv(batch_size, file_path, output_folder):
    """Split CSV into smaller chunks based on batch size."""
    filename_no_ext = os.path.splitext(os.path.basename(file_path))[0]
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        batch = []
        count = 0
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        for i, row in enumerate(reader):
            batch.append(row)
            if (i + 1) % batch_size == 0:
                output_filename = os.path.join(output_folder, f"{filename_no_ext}_chunk#{count+1}.csv")
                with open(output_filename, mode='w', newline='') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerows(batch)
                batch = []
                count += 1
        if batch:
            output_filename = os.path.join(output_folder, f"{filename_no_ext}_chunk#{count+1}.csv")
            with open(output_filename, mode='w', newline='') as outfile:
                writer = csv.writer(outfile)
                writer.writerows(batch)

def start_splitting():
    """Start the CSV splitting process with provided settings."""
    directory = "recipients"
    filename = find_csv_filename(directory)
    if filename:
        batch_size = int(batch_size_entry.get())
        file_path = os.path.join(directory, filename)
        output_folder = os.path.join(directory, "split")
        split_csv(batch_size, file_path, output_folder)
        result_label.config(text=f"Splitting done. Files are in {output_folder}")
    else:
        result_label.config(text="No CSV file found in the directory.")

root = tk.Tk()
root.title("Campaign Management")
root.geometry("600x600")

left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

middle_frame = tk.Frame(root)
middle_frame.pack(side=tk.TOP)

right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

tk.Button(left_frame, text="Open Website", command=open_website).pack(pady=10)
tk.Button(left_frame, text="Open Camp", command=open_camp).pack(pady=10)
tk.Label(left_frame, text="Enter Batch Size:").pack(pady=10)
batch_size_entry = tk.Entry(left_frame)
batch_size_entry.pack(pady=10)
split_button = tk.Button(left_frame, text="Split CSV", command=start_splitting)
split_button.pack(pady=10)
result_label = tk.Label(left_frame, text="")
result_label.pack(pady=10)

tk.Label(middle_frame, text="Select Message Template:").pack(pady=1)
template_id_combobox = ttk.Combobox(middle_frame)
template_id_combobox.pack(pady=10)
refresh_button = tk.Button(middle_frame, text="Refresh", command=init_template_id_list)
refresh_button.pack(pady=10)

tk.Label(right_frame, text="Selected Sender(s):").pack(pady=1)
selected_senders_entry = tk.Entry(right_frame)
selected_senders_entry.pack(pady=10)
tk.Label(right_frame, text="Select Sender(s):").pack(pady=1)
sender_listbox = tk.Listbox(right_frame, selectmode=tk.MULTIPLE)
sender_listbox.pack(pady=10)
refresh_button = tk.Button(right_frame, text="Refresh", command=init_sender_id_listbox)
refresh_button.pack(pady=10)


tk.Label(left_frame, text="Enter Gap between chunks in seconds:").pack(pady=1)
gap_entry = tk.Entry(left_frame)
gap_entry.pack(pady=10)


tk.Label(right_frame, text="Select Starting Hour:").pack(pady=1)
start_hour_combo = ttk.Combobox(right_frame, values=[f"{str(i).zfill(2)}:00" for i in range(24)])
start_hour_combo.set("Select Starting Hour")
start_hour_combo.pack(pady=5)

tk.Label(right_frame, text="Select Ending Hour:").pack(pady=1)
end_hour_combo = ttk.Combobox(right_frame, values=[f"{str(i).zfill(2)}:00" for i in range(24)])
end_hour_combo.set("Select Ending Hour")
end_hour_combo.pack(pady=5)

# Date selection integration using arrays for years, months, and days
years = [str(year) for year in range(2024, 2034)]
months = [str(month) for month in range(1, 13)]
days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

tk.Label(left_frame, text="Select Start Date:").pack(pady=10)
start_year_combo = ttk.Combobox(left_frame, values=years, state="readonly")
start_month_combo = ttk.Combobox(left_frame, values=months, state="readonly")
start_day_combo = ttk.Combobox(left_frame, state="readonly")
start_year_combo.pack(pady=2)
start_month_combo.pack(pady=2)
start_day_combo.pack(pady=2)
start_year_combo.set(years[0])
start_month_combo.set(months[0])
start_year_combo.bind('<<ComboboxSelected>>', update_days)
start_month_combo.bind('<<ComboboxSelected>>', update_days)

# End Date Selection Components
tk.Label(left_frame, text="Select End Date:").pack(pady=10)
end_year_combo = ttk.Combobox(left_frame, values=years, state="readonly")
end_month_combo = ttk.Combobox(left_frame, values=months, state="readonly")
end_day_combo = ttk.Combobox(left_frame, state="readonly")
end_year_combo.pack(pady=2)
end_month_combo.pack(pady=2)
end_day_combo.pack(pady=2)
end_year_combo.set(years[0])
end_month_combo.set(months[0])
end_year_combo.bind('<<ComboboxSelected>>', update_days)
end_month_combo.bind('<<ComboboxSelected>>', update_days)




update_days()

root.mainloop()
