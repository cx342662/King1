from pathlib import Path
import sys

root = Path(sys.argv[1])
home = root / 'app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java'
text = home.read_text(encoding='utf-8')

# Imports
text = text.replace('import com.fongmi.android.tv.bean.Cache;\n', 'import com.fongmi.android.tv.bean.Cache;\nimport com.fongmi.android.tv.bean.Channel;\nimport com.fongmi.android.tv.bean.Group;\n')
text = text.replace('import com.fongmi.android.tv.ui.presenter.HistoryPresenter;\n', 'import com.fongmi.android.tv.ui.presenter.HistoryPresenter;\nimport com.fongmi.android.tv.ui.presenter.HomeLivePresenter;\n')
text = text.replace('import com.fongmi.android.tv.utils.ResUtil;\n', 'import com.fongmi.android.tv.utils.ResUtil;\nimport com.fongmi.android.tv.utils.Task;\n')

# Listener interface
text = text.replace(
    'public class HomeActivity extends BaseActivity implements CustomTitleView.Listener, VodPresenter.OnClickListener, FuncPresenter.OnClickListener, HistoryPresenter.OnClickListener {',
    'public class HomeActivity extends BaseActivity implements CustomTitleView.Listener, VodPresenter.OnClickListener, FuncPresenter.OnClickListener, HistoryPresenter.OnClickListener, HomeLivePresenter.OnClickListener {'
)

# Fields
text = text.replace(
    '    private ArrayObjectAdapter mFuncAdapter;\n    private ArrayObjectAdapter mAdapter;\n',
    '    private ArrayObjectAdapter mFuncAdapter;\n    private ArrayObjectAdapter mLiveAdapter;\n    private ArrayObjectAdapter mAdapter;\n'
)

# Add presenter selector
needle = '        selector.addPresenter(ListRow.class, new CustomRowPresenter(16, FocusHighlight.ZOOM_FACTOR_SMALL, HorizontalGridView.FOCUS_SCROLL_ALIGNED), HistoryPresenter.class);\n'
text = text.replace(needle, needle + '        selector.addPresenter(ListRow.class, new CustomRowPresenter(16), HomeLivePresenter.class);\n')

# Ensure live row is rebuilt after recommendations are added
text = text.replace(
    '    private void addVideo(Result result) {\n        Style style = result.getStyle(getHome().getStyle());\n        if (style.isList()) mAdapter.addAll(mAdapter.size(), result.getList());\n        else addGrid(result.getList(), style);\n    }',
    '    private void addVideo(Result result) {\n        Style style = result.getStyle(getHome().getStyle());\n        if (style.isList()) mAdapter.addAll(mAdapter.size(), result.getList());\n        else addGrid(result.getList(), style);\n        loadHomeLive();\n    }'
)

# Add LIVE event handling without changing the original live initialization path
text = text.replace(
    '            case COMMON:\n                setFunc();\n                break;\n',
    '            case COMMON:\n                setFunc();\n                break;\n            case LIVE:\n                setFunc();\n                loadHomeLive();\n                break;\n'
)

# Add methods before setLogo
marker = '    private void setLogo() {\n'
insert = '''    private void loadHomeLive() {\n        Task.execute(() -> {\n            LiveConfig.get().ensureLoaded();\n            List<Channel> channels = new ArrayList<>();\n            for (Group group : LiveConfig.get().getHome().getGroups()) {\n                if (group.isKeep() || group.isHidden() || group.isEmpty()) continue;\n                channels.addAll(group.getChannel());\n                break;\n            }\n            App.post(() -> setHomeLive(channels));\n        });\n    }\n\n    private void setHomeLive(List<Channel> items) {\n        removeHomeLive();\n        if (items == null || items.isEmpty()) return;\n        mAdapter.add(R.string.home_live);\n        mLiveAdapter = new ArrayObjectAdapter(new HomeLivePresenter(this));\n        mLiveAdapter.addAll(0, items);\n        mAdapter.add(new ListRow(mLiveAdapter));\n    }\n\n    private void removeHomeLive() {\n        int index = mAdapter.indexOf(R.string.home_live);\n        if (index < 0) return;\n        int count = Math.min(2, mAdapter.size() - index);\n        if (count > 0) mAdapter.removeItems(index, count);\n    }\n\n'''
text = text.replace(marker, insert + marker)

# Safe click: enter original LiveActivity only
click_marker = '    @Override\n    public void onItemClick(History item) {\n'
click_impl = '''    @Override\n    public void onItemClick(Channel item) {\n        LiveActivity.start(this);\n    }\n\n'''
text = text.replace(click_marker, click_impl + click_marker)

home.write_text(text, encoding='utf-8')

presenter = root / 'app/src/leanback/java/com/fongmi/android/tv/ui/presenter/HomeLivePresenter.java'
presenter.parent.mkdir(parents=True, exist_ok=True)
presenter.write_text(r'''package com.fongmi.android.tv.ui.presenter;

import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.leanback.widget.Presenter;

import com.bumptech.glide.Glide;
import com.fongmi.android.tv.bean.Channel;
import com.fongmi.android.tv.utils.ResUtil;

public class HomeLivePresenter extends Presenter {

    private final OnClickListener listener;

    public HomeLivePresenter(OnClickListener listener) {
        this.listener = listener;
    }

    public interface OnClickListener {
        void onItemClick(Channel item);
    }

    private static GradientDrawable background(boolean focused) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(Color.rgb(36, 36, 36));
        drawable.setCornerRadius(ResUtil.dp2px(8));
        drawable.setStroke(ResUtil.dp2px(focused ? 3 : 1), focused ? Color.rgb(229, 9, 20) : Color.rgb(74, 74, 74));
        return drawable;
    }

    @NonNull
    @Override
    public Presenter.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent) {
        LinearLayout root = new LinearLayout(parent.getContext());
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setFocusable(true);
        root.setClickable(true);
        root.setPadding(ResUtil.dp2px(10), ResUtil.dp2px(8), ResUtil.dp2px(10), ResUtil.dp2px(6));
        root.setLayoutParams(new ViewGroup.LayoutParams(ResUtil.dp2px(188), ResUtil.dp2px(112)));
        root.setBackground(background(false));

        ImageView logo = new ImageView(parent.getContext());
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        LinearLayout.LayoutParams logoParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ResUtil.dp2px(72));
        root.addView(logo, logoParams);

        TextView name = new TextView(parent.getContext());
        name.setTextColor(Color.WHITE);
        name.setTextSize(14);
        name.setGravity(Gravity.CENTER);
        name.setSingleLine(true);
        LinearLayout.LayoutParams nameParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ResUtil.dp2px(26));
        root.addView(name, nameParams);

        Holder holder = new Holder(root, logo, name);
        root.setOnFocusChangeListener((v, focused) -> {
            v.setBackground(background(focused));
            v.setScaleX(focused ? 1.04f : 1.0f);
            v.setScaleY(focused ? 1.04f : 1.0f);
        });
        return holder;
    }

    @Override
    public void onBindViewHolder(@NonNull Presenter.ViewHolder viewHolder, Object object) {
        Holder holder = (Holder) viewHolder;
        Channel item = (Channel) object;
        holder.name.setText(item.getShow());
        item.loadLogo(holder.logo);
        holder.view.setOnClickListener(v -> listener.onItemClick(item));
    }

    @Override
    public void onUnbindViewHolder(@NonNull Presenter.ViewHolder viewHolder) {
        Holder holder = (Holder) viewHolder;
        Glide.with(holder.logo).clear(holder.logo);
        holder.view.setOnClickListener(null);
    }

    private static class Holder extends Presenter.ViewHolder {
        private final ImageView logo;
        private final TextView name;

        private Holder(LinearLayout root, ImageView logo, TextView name) {
            super(root);
            this.logo = logo;
            this.name = name;
        }
    }
}
''', encoding='utf-8')

print('catTV home live patch applied')
