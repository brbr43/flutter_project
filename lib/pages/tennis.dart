import 'package:campoundnew/api/TennisBookingAPI.dart';
import 'package:campoundnew/auth/AuthCubit.dart';
import 'package:campoundnew/widget/DateSelector.dart';
import 'package:campoundnew/widget/buildSubmitButton.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest_all.dart' as tz;

class Tennis extends StatefulWidget {
  const Tennis({super.key});

  @override
  _TennisState createState() => _TennisState();
}

class _TennisState extends State<Tennis> {
  final TennisBookingAPI api = TennisBookingAPI();
  final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
      FlutterLocalNotificationsPlugin();

  DateTime? selectedDate;
  String? selectedStartTime;
  String? selectedEndTime;

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
    '18:00 PM'
  ];
  List<String> endTimes = [
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
    '19:00 PM',
  ];

  @override
  void initState() {
    super.initState();
    _initializeNotifications();
  }

  void _initializeNotifications() {
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    final InitializationSettings initializationSettings =
        InitializationSettings(android: initializationSettingsAndroid);

    flutterLocalNotificationsPlugin.initialize(initializationSettings);
  }

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
            'Tennis',
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
                        if (selectedDate == null || selectedStartTime == null) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content:
                                    Text("❗ Please select a date and time.")),
                          );
                          return;
                        }

                        String reservationDate =
                            DateFormat('yyyy-MM-dd').format(selectedDate!);
                        String startTime = selectedStartTime!;
                        String endTime = selectedEndTime ?? "15:00";

                        final token =
                            await context.read<AuthCubit>().getStoredToken();

                        bool success = await api.addBooking(
                            reservationDate, startTime, endTime, token!);

                        if (success) {
                          _scheduleNotification(selectedDate!, startTime);

                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text(
                                  "🎉 Your reservation has been completed successfully!"),
                              backgroundColor: Colors.green,
                              duration: Duration(seconds: 3),
                            ),
                          );
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text(
                                  "❌ Reservation failed. The selected time is already reserved. Please choose another time."),
                              backgroundColor: Colors.red,
                              duration: Duration(seconds: 3),
                            ),
                          );
                        }
                      },
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _scheduleNotification(DateTime date, String startTime) async {
    if (await Permission.scheduleExactAlarm.isDenied) {
      print("❌ لا تملك إذن SCHEDULE_EXACT_ALARM");
      return;
    }

    tz.initializeTimeZones();
    DateTime bookingTime = DateFormat('hh:mm a').parse(startTime);
    DateTime fullDateTime = DateTime(
        date.year, date.month, date.day, bookingTime.hour, bookingTime.minute);

    DateTime reminderTime = fullDateTime.subtract(const Duration(hours: 3));
    if (reminderTime.isBefore(DateTime.now())) return;

    await flutterLocalNotificationsPlugin.zonedSchedule(
      0,
      "تذكير بالحجز 🎾",
      "لديك حجز للتنس الساعة $startTime",
      tz.TZDateTime.from(reminderTime, tz.local),
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'tennis_reminder_channel',
          'تذكير الحجز',
          importance: Importance.high,
          priority: Priority.high,
        ),
      ),
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
    );
  }

  Widget _buildStartTimeDropdown(String label, IconData icon, double spacing) {
    return Row(
      children: [
        const SizedBox(width: 15),
        Text(label, style: const TextStyle(fontSize: 20)),
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
      ],
    );
  }

  Widget _buildEndTimeDropdown(String label, IconData icon, double spacing) {
    return Row(
      children: [
        const SizedBox(width: 15),
        Text(label, style: const TextStyle(fontSize: 20)),
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
      ],
    );
  }

  void _updateEndTimes(String startTime) {
    int startIndex = startTimes.indexOf(startTime);
    endTimes = startTimes.sublist(startIndex + 1); // أوقات بعد وقت البداية فقط
  }
}
