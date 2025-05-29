import 'package:campoundnew/api/ApiServiceBooking.dart';
import 'package:campoundnew/auth/AuthCubit.dart';
import 'package:flutter/material.dart';
import 'package:campoundnew/model/BookingData.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class Activity extends StatefulWidget {
  @override
  _ActivityState createState() => _ActivityState();
}

class _ActivityState extends State<Activity> {
  late Future<BookingData?> bookingsFuture =
      Future.value(null); // Initialize with null

  @override
  void initState() {
    super.initState();
    bookingsFuture = Future.value(null);
    _loadactivity();
  }

  Future<void> _loadactivity() async {
    String? token = await context.read<AuthCubit>().getStoredToken();
    if (token != null) {
      setState(() {
        bookingsFuture = ApiServiceBooking().fetchBookings(token);
      });
    } else {
      print("❌ Token not found!");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Activities'),
        centerTitle: true,
        backgroundColor: const Color.fromARGB(255, 47, 7, 226),
      ),
      body: FutureBuilder<BookingData?>(
        future: bookingsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }

          if (snapshot.hasData) {
            var bookingData = snapshot.data!;

            return ListView(
              children: [
                ...buildBookingList(
                    bookingData.tennisBookings, 'Tennis Booking'),
                ...buildBookingList(bookingData.gymBookings, 'Gym Booking'),
                ...buildBookingList(bookingData.partyBookings, 'Party Booking'),
              ],
            );
          }

          return Center(child: Text('No bookings found.'));
        },
      ),
    );
  }

  List<Widget> buildBookingList(List<dynamic> bookings, String bookingType) {
    return bookings.map((booking) {
      return Card(
        margin: EdgeInsets.symmetric(vertical: 8, horizontal: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        elevation: 4,
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                bookingType,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.blueAccent,
                ),
              ),
              SizedBox(height: 8),
              if (booking is TennisBooking || booking is GymBooking)
                Text('Date: ${booking.reservationDate}'),
              if (booking is PartyBooking) Text('Date: ${booking.partyDate}'),
              Text('Start Time: ${booking.startTime}'),
              Text('End Time: ${booking.endTime}'),
              if (bookingType == 'Party Booking') ...[
                Text('Reason: ${booking.reason}'),
                Text('Guests Count: ${booking.guestsCount}'),
              ],
              SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  // Edit Button
                  IconButton(
                    icon: Icon(Icons.edit, color: Colors.blueAccent),
                    onPressed: () {
                      _editBooking(booking, bookingType);
                    },
                  ),
                  // Delete Button
                  IconButton(
                    icon: Icon(Icons.delete, color: Colors.red),
                    onPressed: () {
                      _deleteBooking(booking, bookingType);
                    },
                  ),
                ],
              ),
            ],
          ),
        ),
      );
    }).toList();
  }

  // Edit booking (show popup dialog)
  // Edit booking (show popup dialog)
  Future<void> _editBooking(dynamic booking, String bookingType) async {
    String? token = await context.read<AuthCubit>().getStoredToken();
    if (token != null) {
      TextEditingController startTimeController =
          TextEditingController(text: booking.startTime);
      TextEditingController endTimeController =
          TextEditingController(text: booking.endTime);
      TextEditingController dateController = TextEditingController(
          text: booking.reservationDate); // إضافة حقل التاريخ

      showDialog(
        context: context,
        builder: (context) {
          return AlertDialog(
            title: Text('Edit Booking'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // تاريخ الحجز
                TextField(
                  controller: dateController,
                  decoration: InputDecoration(
                      labelText: 'Date (YYYY-MM-DD)'), // تنسيق التاريخ
                ),
                // وقت البداية
                TextField(
                  controller: startTimeController,
                  decoration: InputDecoration(labelText: 'Start Time'),
                ),
                // وقت النهاية
                TextField(
                  controller: endTimeController,
                  decoration: InputDecoration(labelText: 'End Time'),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: Text('Cancel'),
              ),
              TextButton(
                onPressed: () async {
                  // جمع البيانات المعدلة
                  Map<String, dynamic> updatedData = {
                    'booking_type': bookingType, // إضافة نوع الحجز

                    'reservation_date':
                        dateController.text, // إضافة التاريخ المعدل
                    'start_time': startTimeController.text,
                    'end_time': endTimeController.text,
                  };

                  // إرسال التعديل إلى API
                  bool success = await ApiServiceBooking().updateBooking(
                    token,
                    bookingType,
                    booking.id,
                    updatedData,
                  );

                  if (success) {
                    print("✅ تم تعديل الحجز بنجاح!");
                    _loadactivity();
                    Navigator.pop(context);
                  } else {
                    print("❌ فشل في تعديل الحجز.");
                  }
                },
                child: Text('Save'),
              ),
            ],
          );
        },
      );
    }
  }

  // Delete booking (confirmation dialog)
  Future<void> _deleteBooking(dynamic booking, String bookingType) async {
    String? token = await context.read<AuthCubit>().getStoredToken();
    if (token != null) {
      showDialog(
        context: context,
        builder: (context) {
          return AlertDialog(
            title: Text('Confirm Deletion'),
            content: Text('Are you sure you want to delete this booking?'),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: Text('Cancel'),
              ),
              TextButton(
                onPressed: () async {
                  bool success = await ApiServiceBooking().deleteBooking(
                    token,
                    bookingType,
                    booking.id,
                  );

                  if (success) {
                    print("✅ تم حذف الحجز بنجاح!");
                    _loadactivity();
                    Navigator.pop(context);
                  } else {
                    print("❌ فشل في حذف الحجز.");
                    Navigator.pop(context);
                  }
                },
                child: Text('Delete'),
              ),
            ],
          );
        },
      );
    }
  }
}
