import 'package:campoundnew/api/PartyBooking.dart';
import 'package:campoundnew/auth/AuthCubit.dart';
import 'package:campoundnew/widget/DateSelector.dart';
import 'package:campoundnew/widget/buildSubmitButton.dart';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

class Party extends StatefulWidget {
  const Party({super.key});

  @override
  State<Party> createState() => _PartyState();
}

class _PartyState extends State<Party> {
  final Partybooking api = Partybooking();
  DateTime? selectedDate;
  String? selectedStartTime;
  String? selectedEndTime;
  int? guestsCount; // تغيير النوع إلى int
  String? eventReason;

  final List<String> startTimes = [
    '07:00 AM',
    '08:00 AM',
    '09:00 AM',
    '10:00 AM',
    '11:00 AM',
    '12:00 PM',
    '13:00 PM',
    '14:00 PM',
    '15:00 PM',
    '16:00 PM',
    '17:00 PM',
    '18:00 PM',
  ];
  List<String> endTimes = [];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white, size: 40),
          onPressed: () {
            Navigator.pop(context);
          },
        ),
        title: const Center(
          child: Text(
            'party',
            style: TextStyle(
                fontSize: 20, color: Colors.white, fontFamily: 'Pacifico'),
          ),
        ),
        backgroundColor: const Color.fromARGB(255, 47, 7, 226),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 20),
              DateSelector(
                label: 'Date',
                icon: Icons.calendar_today,
                spacing: 60,
                selectedDate: selectedDate,
                onDateSelected: (DateTime newDate) {
                  setState(() {
                    selectedDate = newDate;
                  });
                },
              ),
              SizedBox(
                height: 20,
              ),
              _buildInputRow('Guests number', Icons.people, 0, (value) {
                setState(() {
                  guestsCount = int.tryParse(value); // تحويل القيمة إلى int
                });
              }),
              const SizedBox(height: 20),
              _buildInputRow('Event Type', Icons.event, 10.0, (value) {
                setState(() {
                  eventReason = value;
                });
              }),
              const SizedBox(height: 20),
              _buildStartTimeDropdown('Start Time', Icons.access_time, 20.0),
              const SizedBox(height: 20),
              _buildEndTimeDropdown('End Time', Icons.access_time, 20.0),
              const SizedBox(height: 40),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  Flexible(
                    flex: 1,
                    child: BuildSubmitButton(
                        text: 'Send',
                        onPressed: () async {
                          String reservationDate = selectedDate != null
                              ? DateFormat('yyyy-MM-dd').format(selectedDate!)
                              : "2024-11-13"; // التاريخ الافتراضي إذا لم يتم اختيار تاريخ
                          String startTime = selectedStartTime ?? "14:00";
                          String endTime = selectedEndTime ?? "15:00";
                          String reason = eventReason ?? ""; // السبب (من الحقل)
                          int guests =
                              guestsCount ?? 0; // عدد الضيوف (من الحقل)

                          final token =
                              await context.read<AuthCubit>().getStoredToken();

                          bool success = await api.addBooking(
                            reservationDate,
                            reason,
                            guests,
                            startTime,
                            endTime,
                            token!,
                          );

                          if (success) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                    "🎉 Your party has been successfully booked!"),
                                backgroundColor: Colors.green,
                              ),
                            );
                          } else {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                    "❌ Reservation failed. The selected time is already reserved. Please choose another time."),
                                backgroundColor: Colors.red,
                              ),
                            );
                          }
                        }),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  // Helper method to create input rows
  Widget _buildInputRow(
      String label, IconData icon, double spacing, Function(String) onChanged) {
    return Row(
      children: [
        const SizedBox(width: 15),
        Text(label, style: const TextStyle(fontSize: 16)),
        SizedBox(width: spacing),
        Expanded(
          child: TextField(
            keyboardType: TextInputType.number, // تغيير نوع المدخلات إلى أرقام
            decoration: InputDecoration(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(30.0),
                borderSide: const BorderSide(color: Colors.black),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(30.0),
                borderSide: const BorderSide(color: Colors.black, width: 2),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(30.0),
                borderSide: const BorderSide(color: Colors.blue, width: 2),
              ),
            ),
            onChanged: onChanged,
          ),
        ),
        const SizedBox(width: 15),
        Padding(
          padding: const EdgeInsets.only(right: 10),
          child: Icon(icon, size: 50, color: Colors.black),
        ),
      ],
    );
  }

  // Dropdown for Start Time
  Widget _buildStartTimeDropdown(String label, IconData icon, double spacing) {
    return Row(
      children: [
        const SizedBox(width: 15),
        Text(label, style: const TextStyle(fontSize: 16)),
        SizedBox(width: spacing),
        Expanded(
          child: DropdownButtonFormField<String>(
            decoration: InputDecoration(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(30.0),
                borderSide: const BorderSide(color: Colors.black),
              ),
            ),
            value: selectedStartTime,
            items: startTimes.map((time) {
              return DropdownMenuItem(
                value: time,
                child: Text(time),
              );
            }).toList(),
            onChanged: (value) {
              setState(() {
                selectedStartTime = value;
                _updateEndTimes(value!);
                selectedEndTime = null;
              });
            },
          ),
        ),
        const SizedBox(width: 15),
        Padding(
          padding: const EdgeInsets.only(right: 10),
          child: Icon(icon, size: 50, color: Colors.black),
        ),
      ],
    );
  }

  // Dropdown for End Time
  Widget _buildEndTimeDropdown(String label, IconData icon, double spacing) {
    return Row(
      children: [
        const SizedBox(width: 15),
        Text(label, style: const TextStyle(fontSize: 18)),
        SizedBox(width: spacing),
        Expanded(
          child: DropdownButtonFormField<String>(
            decoration: InputDecoration(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(30.0),
                borderSide: const BorderSide(color: Colors.black),
              ),
            ),
            value: selectedEndTime,
            items: endTimes.map((time) {
              return DropdownMenuItem(
                value: time,
                child: Text(time),
              );
            }).toList(),
            onChanged: (value) {
              setState(() {
                selectedEndTime = value;
              });
            },
          ),
        ),
        const SizedBox(width: 15),
        Padding(
          padding: const EdgeInsets.only(right: 10),
          child: Icon(icon, size: 50, color: Colors.black),
        ),
      ],
    );
  }

  void _updateEndTimes(String startTime) {
    int startIndex = startTimes.indexOf(startTime);
    endTimes = startTimes.sublist(startIndex + 1); // أوقات بعد وقت البداية فقط
  }
}
