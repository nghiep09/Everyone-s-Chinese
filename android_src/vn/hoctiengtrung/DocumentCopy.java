package vn.hoctiengtrung;

import android.content.Context;
import android.net.Uri;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.IOException;

/** Copies ONLY the document explicitly selected by the user. */
public final class DocumentCopy {
    public static void copy(Context context, String uri, String destination) throws IOException {
        File file = new File(destination);
        boolean success = false;
        try (InputStream input = context.getContentResolver().openInputStream(Uri.parse(uri));
             FileOutputStream output = new FileOutputStream(file)) {
            if (input == null) throw new IOException("Không đọc được tài liệu.");
            byte[] buffer = new byte[32768];
            int count;
            long total = 0;
            while ((count = input.read(buffer)) != -1) {
                total += count;
                if (total > 20L * 1024L * 1024L) throw new IOException("File vượt quá 20 MB.");
                output.write(buffer, 0, count);
            }
            success = true;
        } finally {
            if (!success) file.delete();
        }
    }
}
