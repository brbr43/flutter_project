import 'package:campoundnew/admin_pages/apiadmin/complaintapi.dart';
import 'package:campoundnew/auth/AuthCubitadmin.dart';
import 'package:campoundnew/model/complaintBooking.dart';
import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class ComplaintPage extends StatefulWidget {
  const ComplaintPage({super.key});

  @override
  _ComplaintPageState createState() => _ComplaintPageState();
}

class _ComplaintPageState extends State<ComplaintPage> {
  final Complaintapi complaintapi = Complaintapi();
  late Future<List<Complaintbooking>> futureComplaints = Future.value([]);

  @override
  void initState() {
    super.initState();
    _loadComplaints();
  }

  Future<void> _loadComplaints() async {
    final token = await context.read<Authcubitadmin>().getStoredToken();
    setState(() {
      futureComplaints = complaintapi
          .fetchComplaints(token!); // تغيير الاسم إلى fetchComplaints
    });
  }

  void _deleteComplaint(BuildContext context, String token, int id) async {
    await complaintapi.deleteComplaint(token, id); // تغيير إلى deleteComplaint
    _loadComplaints(); // إعادة تحميل البيانات بعد الحذف
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Complaint deleted successfully')),
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
            'Show Complaints',
            style: TextStyle(
              fontSize: 20,
              color: Colors.white,
              fontFamily: 'Pacifico',
            ),
          ),
        ),
        backgroundColor: const Color.fromARGB(255, 47, 7, 226),
      ),
      body: FutureBuilder<List<Complaintbooking>>(
        future: futureComplaints,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          } else if (snapshot.hasData) {
            List<Complaintbooking> complaints = snapshot.data!;
            return ListView.builder(
              itemCount: complaints.length,
              itemBuilder: (context, index) {
                Complaintbooking complaint = complaints[index];

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
                          '${complaint.email}:',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Color.fromARGB(
                                255, 0, 0, 0), // اللون الأغمق للبريد الإلكتروني
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          '${complaint.message}',
                          style: const TextStyle(
                            fontSize: 16, // حجم أصغر للرسالة
                            color: Colors.black87, // اللون الأسود الغامق
                          ),
                        ),
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
                                _deleteComplaint(context, token!, complaint.id);
                              },
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
            return const Center(child: Text('No complaints available.'));
          }
        },
      ),
    );
  }
}
