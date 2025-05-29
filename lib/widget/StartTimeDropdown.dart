import 'package:flutter/material.dart';

// Widget للقائمة المنسدلة لوقت البدء
// Widget للقائمة المنسدلة لوقت البدء
class StartTimeDropdown extends StatelessWidget {
  final String label;
  final IconData icon;
  final double spacing;

  const StartTimeDropdown({
    super.key,
    required this.label,
    required this.icon,
    required this.spacing,
    required Null Function(String? value) onChanged,
  });

  @override
  Widget build(BuildContext context) {
    List<String> startTimes = [
      '7:00 AM',
      '8:00 AM',
      '9:00 AM',
      '10:00 AM',
      '11:00 AM',
      '12:00 PM',
      '1:00 PM',
      '2:00 PM',
      '3:00 PM',
      '4:00 PM',
      '5:00 PM',
      '6:00 PM',
    ];

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
              ),
            ),
            items: startTimes.map((time) {
              return DropdownMenuItem(value: time, child: Text(time));
            }).toList(),
            onChanged: (value) {},
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(right: 10),
          child: Icon(icon, size: 50, color: Colors.black),
        ),
      ],
    );
  }
}

// Widget للقائمة المنسدلة لوقت الانتهاء
class EndTimeDropdown extends StatelessWidget {
  final String label;
  final IconData icon;
  final double spacing;

  const EndTimeDropdown({
    super.key,
    required this.label,
    required this.icon,
    required this.spacing,
    required Null Function(String? value) onChanged,
  });

  @override
  Widget build(BuildContext context) {
    List<String> endTimes = [
      '8:00 AM',
      '9:00 AM',
      '10:00 AM',
      '11:00 AM',
      '12:00 PM',
      '1:00 PM',
      '2:00 PM',
      '3:00 PM',
      '4:00 PM',
      '5:00 PM',
      '6:00 PM',
      '7:00 PM',
    ];

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
              ),
            ),
            items: endTimes.map((time) {
              return DropdownMenuItem(value: time, child: Text(time));
            }).toList(),
            onChanged: (value) {},
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(right: 10),
          child: Icon(icon, size: 50, color: Colors.black),
        ),
      ],
    );
  }
}
