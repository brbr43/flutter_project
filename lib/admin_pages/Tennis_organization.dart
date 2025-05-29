import 'package:campoundnew/admin_pages/apiadmin/Tennisapi.dart';
import 'package:campoundnew/auth/AuthCubitadmin.dart';
import 'package:campoundnew/model/TennisBooking.dart';
import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class TennisOrganization extends StatefulWidget {
  const TennisOrganization({super.key});

  @override
  _TennisOrganizationState createState() => _TennisOrganizationState();
}

class _TennisOrganizationState extends State<TennisOrganization> {
  final Tennisapi tennisapi = Tennisapi();
  late Future<List<Tennisbooking>> futureBookings = Future.value([]);

  @override
  void initState() {
    super.initState();
    _loadBookings();
  }

  Future<void> _loadBookings() async {
    final token = await context.read<Authcubitadmin>().getStoredToken();
    setState(() {
      futureBookings = tennisapi.fetchBookings(token!);
    });
  }

  void _deleteBooking(BuildContext context, String token, int id) async {
    await tennisapi.deleteBooking(token, id);
    _loadBookings(); // إعادة تحميل البيانات بعد الحذف
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Booking deleted successfully')),
    );
  }

  void _showUpdateDialog(BuildContext context, Tennisbooking booking) async {
    TextEditingController dateController =
        TextEditingController(text: booking.reservationDate);
    TextEditingController startController =
        TextEditingController(text: booking.startTime);
    TextEditingController endController =
        TextEditingController(text: booking.endTime);
    TextEditingController emailController =
        TextEditingController(text: booking.email);

    final token = await context.read<Authcubitadmin>().getStoredToken();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text("Update Booking"),
          content: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: dateController,
                decoration:
                    const InputDecoration(labelText: 'Reservation Date'),
              ),
              TextField(
                controller: startController,
                decoration: const InputDecoration(labelText: 'Start Time'),
              ),
              TextField(
                controller: endController,
                decoration: const InputDecoration(labelText: 'End Time'),
              ),
              TextField(
                controller: emailController,
                decoration: const InputDecoration(labelText: 'Email'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
              },
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                Tennisbooking updatedBooking = Tennisbooking(
                  id: booking.id,
                  userId: booking.userId,
                  reservationDate: dateController.text,
                  startTime: startController.text,
                  endTime: endController.text,
                  email: emailController.text,
                  createdAt: booking.createdAt,
                  updatedAt: DateTime.now().toString(),
                );
                await tennisapi.updateBooking(
                    token!, booking.id, updatedBooking);
                _loadBookings(); // إعادة تحميل البيانات بعد التعديل
                Navigator.pop(context);
              },
              child: const Text('Update'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(
            Icons.arrow_back,
            color: Colors.white,
            size: 40,
          ),
          onPressed: () {
            Navigator.pop(context);
          },
        ),
        title: const Center(
          child: Text(
            'Tennis',
            style: TextStyle(
              fontSize: 20,
              color: Colors.white,
              fontFamily: 'Pacifico',
            ),
          ),
        ),
        backgroundColor: const Color.fromARGB(255, 47, 7, 226),
      ),
      body: FutureBuilder<List<Tennisbooking>>(
        future: futureBookings,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          } else if (snapshot.hasData) {
            List<Tennisbooking> bookings = snapshot.data!;
            return ListView.builder(
              itemCount: bookings.length,
              itemBuilder: (context, index) {
                Tennisbooking booking = bookings[index];

                return Card(
                  margin:
                      const EdgeInsets.symmetric(vertical: 10, horizontal: 15),
                  elevation: 5,
                  child: Padding(
                    padding: const EdgeInsets.all(15.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Reservation Date: ${booking.reservationDate}',
                          style: const TextStyle(
                              fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 5),
                        Text('Start Time: ${booking.startTime}'),
                        Text('End Time: ${booking.endTime}'),
                        Text('Email: ${booking.email}'),
                        const SizedBox(height: 10),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            IconButton(
                              icon: const Icon(Icons.delete, color: Colors.red),
                              onPressed: () async {
                                final token = await context
                                    .read<Authcubitadmin>()
                                    .getStoredToken();
                                _deleteBooking(context, token!, booking.id);
                              },
                            ),
                            IconButton(
                              icon: const Icon(Icons.edit, color: Colors.blue),
                              onPressed: () =>
                                  _showUpdateDialog(context, booking),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
          } else {
            return const Center(child: Text('No data available.'));
          }
        },
      ),
    );
  }
}
