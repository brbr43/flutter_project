import 'package:campoundnew/admin_pages/apiadmin/UsersApi.dart';
import 'package:campoundnew/model/User.dart';
import 'package:flutter/material.dart';

class Users extends StatefulWidget {
  const Users({super.key});

  @override
  _UsersState createState() => _UsersState();
}

class _UsersState extends State<Users> {
  late Future<List<User>> _usersFuture;

  @override
  void initState() {
    super.initState();
    _usersFuture = UsersApi().getUsers(); // تحميل البيانات عند التهيئة
  }

  // دالة لحذف مستخدم
  void _deleteUser(BuildContext context, String userId) {
    UsersApi().deleteUser(userId).then((_) {
      // بعد الحذف، يمكنك تحديث واجهة المستخدم (مثلاً عبر إعادة تحميل البيانات)
      setState(() {
        _usersFuture = UsersApi().getUsers(); // إعادة تحميل البيانات بعد الحذف
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("User deleted successfully!")),
      );
    }).catchError((e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error: $e")),
      );
    });
  }

  // دالة لتحديث بيانات مستخدم
  void _updateUser(BuildContext context, User user) {
    TextEditingController emailController =
        TextEditingController(text: user.email);
    TextEditingController phoneController =
        TextEditingController(text: user.phoneNumber);
    TextEditingController apartmentController =
        TextEditingController(text: user.apartmentNumber.toString());
    TextEditingController complexController =
        TextEditingController(text: user.complexName);

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text("Update User"),
          content: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: emailController,
                decoration: const InputDecoration(labelText: 'Email'),
              ),
              TextField(
                controller: phoneController,
                decoration: const InputDecoration(labelText: 'Phone Number'),
              ),
              TextField(
                controller: apartmentController,
                decoration:
                    const InputDecoration(labelText: 'Apartment Number'),
                keyboardType: TextInputType.number, // لتأكيد إدخال الأرقام فقط
              ),
              TextField(
                controller: complexController,
                decoration: const InputDecoration(labelText: 'Complex Name'),
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
              onPressed: () {
                // استدعاء API لتحديث بيانات المستخدم
                // تحويل قيمة apartmentController إلى int قبل إرسالها
                int apartmentNumber = int.tryParse(apartmentController.text) ??
                    0; // إذا كان النص غير قابل للتحويل، يتم تعيين القيمة 0

                UsersApi()
                    .updateUser(
                  user.id.toString(), // تحويل الـ id من int إلى String
                  emailController.text,
                  phoneController.text,
                  apartmentNumber.toString(), // تحويل الرقم إلى نص عند الإرسال
                  complexController.text,
                )
                    .then((_) {
                  setState(() {
                    _usersFuture = UsersApi()
                        .getUsers(); // إعادة تحميل البيانات بعد التحديث
                  });
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("User updated successfully!")),
                  );
                }).catchError((e) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("Error: $e")),
                  );
                });
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
            Navigator.pop(context); // Return to the previous page
          },
        ),
        title: const Center(
          child: Text(
            'Show Users',
            style: TextStyle(
              fontSize: 20,
              color: Colors.white,
              fontFamily: 'Pacifico',
            ),
          ),
        ),
        backgroundColor: const Color.fromARGB(255, 47, 7, 226),
      ),
      body: FutureBuilder<List<User>>(
        future: _usersFuture, // استخدام المتغير الذي يحمل البيانات
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('خطأ: ${snapshot.error}'));
          } else if (snapshot.hasData) {
            List<User> users = snapshot.data!;

            return ListView.builder(
              itemCount: users.length,
              itemBuilder: (context, index) {
                User user = users[index];

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
                          user.email,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text('Phone: ${user.phoneNumber}'),
                        Text('Apartment: ${user.apartmentNumber}'),
                        Text('Complex: ${user.complexName}'),
                        const SizedBox(height: 10),
                        Text('Created At: ${user.createdAt}'),
                        const SizedBox(height: 10),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            IconButton(
                              icon: const Icon(Icons.delete, color: Colors.red),
                              onPressed: () =>
                                  _deleteUser(context, user.id.toString()),
                            ),
                            IconButton(
                              icon: const Icon(Icons.edit, color: Colors.blue),
                              onPressed: () => _updateUser(context, user),
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
            return const Center(child: Text('لا يوجد بيانات لعرضها.'));
          }
        },
      ),
    );
  }
}
