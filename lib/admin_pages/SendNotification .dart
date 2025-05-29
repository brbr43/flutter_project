import 'package:campoundnew/admin_pages/apiadmin/sendNotificationapi.dart';
import 'package:flutter/material.dart';
import 'package:onesignal_flutter/onesignal_flutter.dart';

class SendNotification extends StatefulWidget {
  const SendNotification({super.key});

  @override
  State<SendNotification> createState() => _SendNotificationState();
}

class _SendNotificationState extends State<SendNotification> {
  // تعريف TextEditingController
  TextEditingController _messageController = TextEditingController();

  @override
  void initState() {
    super.initState();

    // تهيئة OneSignal مع App ID الخاص بك
    OneSignal.initialize('4e73f170-afab-4415-be7c-50e3dc09b086');

    // طلب إذن الإشعارات من المستخدم
    checkNotificationPermission();
  }

  void checkNotificationPermission() async {
    bool canRequest = await OneSignal.Notifications.canRequest();
    if (canRequest) {
      OneSignal.Notifications.requestPermission(true).then((accepted) {
        print("Notification permission accepted: $accepted");
      });
    } else {
      print("Cannot request notification permissions.");
    }
  }

  // إظهار نافذة تأكيد قبل إرسال الإشعار
  void showConfirmationDialog(String message) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text("Confirm Notification"),
          content:
              const Text("Are you sure you want to send this notification?"),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(); // إغلاق النافذة المنبثقة
              },
              child: const Text("Cancel"),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(); // إغلاق النافذة المنبثقة
                sendNotification("New Notification", message);
                Future.delayed(Duration.zero, () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                        backgroundColor: Colors.green,
                        content: Text('Notification Sent Successfully!')),
                  );
                });
                // حذف النص من الحقل بعد الإرسال
                setState(() {
                  _messageController.clear();
                });
                FocusScope.of(context)
                    .unfocus(); // إزالة التركيز عن الحقل النصي
              },
              child: const Text(
                "Confirm",
                style: TextStyle(color: Colors.red),
              ),
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
        title: const Center(
          child: Text(
            "Send Notification",
            style: TextStyle(color: Colors.white, fontFamily: 'Pacifico'),
          ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () {
            Navigator.pop(context); // للعودة إلى الصفحة السابقة
          },
        ),
        backgroundColor: const Color.fromARGB(255, 47, 7, 226),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // TextField لكتابة النص
              TextField(
                controller: _messageController,
                decoration: const InputDecoration(
                  labelText: 'Enter your message',
                  border: OutlineInputBorder(),
                ),
                maxLines: 5, // يمكنك تخصيص عدد الأسطر حسب الحاجة
              ),
              const SizedBox(height: 16),
              // زر لإظهار نافذة التأكيد
              ElevatedButton.icon(
                onPressed: () {
                  String message = _messageController.text;
                  if (message.isNotEmpty) {
                    showConfirmationDialog(message);
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Please enter a message')),
                    );
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color.fromARGB(255, 47, 7, 226),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
                icon: const Icon(Icons.send, color: Colors.white),
                label: const Text(
                  "Send Notification",
                  style: TextStyle(fontSize: 16, color: Colors.white),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
