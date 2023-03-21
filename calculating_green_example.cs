
// The circle will change its position based on the drone's velocity, height, and distance to the shooter. The drone can appear from the right or left corner.

// First, create a simple green circle texture in any image editing software and save it as "GreenCircle.png" in your Unity project's "Assets/Resources" folder.

// Then, create a new C# script called "DroneAimingUI" and paste the following code:
// Code is in .\caluclating_green_example.cs 

// Finally, add a Canvas to your scene by right-clicking in the Hierarchy, selecting "UI" > "Canvas". Make sure the "Render Mode" of the Canvas is set to "Screen Space - Camera" and assign the main camera to the "Render Camera" field. Attach the "DroneAimingUI" script to the Canvas GameObject and assign the shooter and drone variables in the script to the corresponding objects in your scene.

// The green circle will now appear on the screen, indicating the aiming point based on the drone's velocity, height, and distance to the shooter.


using UnityEngine;
using UnityEngine.UI;

public class DroneAimingUI : MonoBehaviour
{
    public Transform shooter;
    public Transform drone;
    public float droneVelocity = 55.56f; // in meters per second
    public float bulletMuzzleVelocity = 860f; // in meters per second
    public float circleSize = 0.5f; // Adjust this value to set the circle size on the screen

    private RectTransform greenCircleRectTransform;
    private Image greenCircleImage;

    private void Start()
    {
        GameObject greenCircle = new GameObject("GreenCircle");
        greenCircle.transform.SetParent(transform);

        greenCircleImage = greenCircle.AddComponent<Image>();
        greenCircleImage.sprite = Resources.Load<Sprite>("GreenCircle");

        greenCircleRectTransform = greenCircle.GetComponent<RectTransform>();
        greenCircleRectTransform.sizeDelta = new Vector2(circleSize, circleSize);
        greenCircleRectTransform.anchorMin = new Vector2(0.5f, 0.5f);
        greenCircleRectTransform.anchorMax = new Vector2(0.5f, 0.5f);
    }

    private void Update()
    {
        Vector3 aimingPoint = CalculateAimingPoint(shooter.position, drone.position, droneVelocity, bulletMuzzleVelocity);
        Vector3 screenPoint = Camera.main.WorldToScreenPoint(aimingPoint);
        greenCircleRectTransform.position = screenPoint;
    }

   private Vector3 CalculateAimingPoint(Vector3 shooterPosition, Vector3 dronePosition, float droneVelocity, float bulletMuzzleVelocity)
    {
        float distance = Vector3.Distance(shooterPosition, dronePosition);
        float timeToTarget = distance / bulletMuzzleVelocity;
        float horizontalDroneDisplacement = droneVelocity * timeToTarget;
        float bulletDrop = 0.5f * Physics.gravity.y * timeToTarget * timeToTarget;

        Vector3 droneDirection = drone.forward; // Use the drone's forward vector instead of the right vector
        Vector3 horizontalAimingPoint = dronePosition + droneDirection * horizontalDroneDisplacement;
        Vector3 verticalAdjustment = new Vector3(0, -bulletDrop, 0);

        return horizontalAimingPoint + verticalAdjustment;
    }
}